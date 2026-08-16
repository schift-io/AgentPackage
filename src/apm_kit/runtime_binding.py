from __future__ import annotations

import re
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse


RUNTIME_BINDING_VERSION = "apm.runtime.binding.v1"
RUNTIME_RESOLUTION_VERSION = "apm.runtime.resolution.v1"
GCP_CLOUD_RUN_PROVIDER = "gcp-cloud-run"
AWS_LAMBDA_PROVIDER = "aws-lambda"
CLOUDFLARE_WORKER_PROVIDER = "cloudflare-worker"
VERCEL_EDGE_PROVIDER = "vercel-edge"
SUPABASE_EDGE_PROVIDER = "supabase-edge"

_RUNTIME_REF_PATTERN = re.compile(
    r"^apm://runtime/[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?@"
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
_PROVIDER_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
_CLOUD_RUN_RESOURCE_PATTERN = re.compile(
    r"^projects/[^/]+/locations/[^/]+/services/[^/]+$"
)
_SERVICE_ACCOUNT_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.iam\.gserviceaccount\.com$"
)
_AWS_LAMBDA_ARN_PATTERN = re.compile(
    r"^arn:aws(?:-[a-z]+)?:lambda:[a-z0-9-]+:[0-9]{12}:function:"
    r"[A-Za-z0-9_-]+(?::[A-Za-z0-9_-]+)?$"
)
_CLOUDFLARE_WORKER_RESOURCE_PATTERN = re.compile(
    r"^accounts/[0-9a-f]{32}/workers/services/[A-Za-z0-9][A-Za-z0-9_-]{0,62}$"
)
_VERCEL_EDGE_RESOURCE_PATTERN = re.compile(
    r"^projects/[A-Za-z0-9_-]+/functions/[A-Za-z0-9._/\[\]-]+$"
)
_SUPABASE_EDGE_RESOURCE_PATTERN = re.compile(
    r"^projects/[a-z0-9]{20}/functions/[a-z][a-z0-9-]{0,62}$"
)
_APPLICATION_SECRET_HEADER_PATTERN = re.compile(r"^[A-Za-z0-9-]{1,128}$")
_INVOKE_PATH_PREFIX_PATTERN = re.compile(
    r"^/(?:[A-Za-z0-9][A-Za-z0-9._~-]*)(?:/[A-Za-z0-9][A-Za-z0-9._~-]*)*$"
)


class RuntimeBindingError(ValueError):
    pass


def runtime_ref_problems(value: Any, *, label: str = "runtime_ref") -> list[str]:

    if not isinstance(value, str) or not value.strip():
        return [f"{label} must be a non-empty logical APM runtime URI"]
    if not _RUNTIME_REF_PATTERN.fullmatch(value):
        return [
            f"{label} must match "
            "'apm://runtime/<name>@<semver>' and must not contain a provider URL"
        ]
    return []


def validate_runtime_binding_document(document: Any) -> list[str]:

    if not isinstance(document, dict):
        return ["runtime binding document must be an object"]

    problems: list[str] = []
    _unknown_fields(document, {"version", "bindings"}, "runtime binding document", problems)
    if document.get("version") != RUNTIME_BINDING_VERSION:
        problems.append(
            f"runtime binding document.version must be {RUNTIME_BINDING_VERSION!r}"
        )
    bindings = document.get("bindings")
    if not isinstance(bindings, dict) or not bindings:
        problems.append("runtime binding document.bindings must be a non-empty object")
        return problems

    for runtime_ref, binding in sorted(bindings.items(), key=lambda item: str(item[0])):
        label = f"runtime binding document.bindings[{runtime_ref!r}]"
        problems.extend(runtime_ref_problems(runtime_ref, label=label))
        _validate_binding(binding, label, problems)
    return problems


def resolve_runtime_binding(
    manifest: Mapping[str, Any],
    document: Mapping[str, Any],
    *,
    required_capabilities: Iterable[str] = (),
) -> dict[str, Any]:

    document_problems = validate_runtime_binding_document(document)
    if document_problems:
        raise RuntimeBindingError("; ".join(document_problems))

    runtime_ref = manifest.get("runtime_ref")
    ref_problems = runtime_ref_problems(runtime_ref)
    if ref_problems:
        raise RuntimeBindingError("; ".join(ref_problems))
    assert isinstance(runtime_ref, str)

    bindings = document["bindings"]
    assert isinstance(bindings, dict)
    binding = bindings.get(runtime_ref)
    if not isinstance(binding, dict):
        raise RuntimeBindingError(f"no runtime binding is configured for {runtime_ref!r}")

    required = {
        capability.strip()
        for capability in required_capabilities
        if isinstance(capability, str) and capability.strip()
    }
    provided = set(binding["capabilities"])
    missing = sorted(required - provided)
    if missing:
        raise RuntimeBindingError(
            f"runtime binding {runtime_ref!r} lacks required capabilities {missing}"
        )

    return {
        "protocol": RUNTIME_RESOLUTION_VERSION,
        "runtime_ref": runtime_ref,
        "provider": binding["provider"],
        "resource": binding["resource"],
        "invoke_url": _normalise_https_url(binding["invoke_url"]),
        "auth": dict(binding["auth"]),
        "capabilities": sorted(provided),
        "required_capabilities": sorted(required),
    }


def _validate_binding(value: Any, label: str, problems: list[str]) -> None:
    if not isinstance(value, dict):
        problems.append(f"{label} must be an object")
        return
    _unknown_fields(
        value,
        {"provider", "resource", "invoke_url", "auth", "capabilities"},
        label,
        problems,
    )

    provider = value.get("provider")
    if not isinstance(provider, str) or not _PROVIDER_PATTERN.fullmatch(provider):
        problems.append(f"{label}.provider must be a lowercase provider identifier")

    resource = value.get("resource")
    if not isinstance(resource, str) or not resource.strip():
        problems.append(f"{label}.resource must be a non-empty provider resource identifier")

    invoke_url = value.get("invoke_url")
    try:
        _normalise_https_url(invoke_url)
    except RuntimeBindingError as exc:
        problems.append(f"{label}.invoke_url {exc}")

    _validate_auth(value.get("auth"), label, problems)
    _string_list(value.get("capabilities"), f"{label}.capabilities", problems)

    if provider == GCP_CLOUD_RUN_PROVIDER:
        _validate_cloud_run_binding(value, label, problems)
    elif provider == AWS_LAMBDA_PROVIDER:
        _validate_lambda_binding(value, label, problems)
    elif provider == CLOUDFLARE_WORKER_PROVIDER:
        _validate_http_secret_binding(
            value,
            label,
            problems,
            resource_pattern=_CLOUDFLARE_WORKER_RESOURCE_PATTERN,
            provider=CLOUDFLARE_WORKER_PROVIDER,
        )
    elif provider == VERCEL_EDGE_PROVIDER:
        _validate_http_secret_binding(
            value,
            label,
            problems,
            resource_pattern=_VERCEL_EDGE_RESOURCE_PATTERN,
            provider=VERCEL_EDGE_PROVIDER,
            require_path_prefix=True,
        )
    elif provider == SUPABASE_EDGE_PROVIDER:
        _validate_http_secret_binding(
            value,
            label,
            problems,
            resource_pattern=_SUPABASE_EDGE_RESOURCE_PATTERN,
            provider=SUPABASE_EDGE_PROVIDER,
            require_path_prefix=True,
        )


def _validate_cloud_run_binding(
    binding: Mapping[str, Any], label: str, problems: list[str]
) -> None:
    resource = binding.get("resource")
    if not isinstance(resource, str) or not _CLOUD_RUN_RESOURCE_PATTERN.fullmatch(resource):
        problems.append(
            f"{label}.resource must be "
            "'projects/<project>/locations/<region>/services/<service>' for gcp-cloud-run"
        )

    auth = binding.get("auth")
    if not isinstance(auth, dict):
        return
    if auth.get("type") != "gcp-oidc":
        problems.append(f"{label}.auth.type must be 'gcp-oidc' for gcp-cloud-run")
        return
    audience = auth.get("audience")
    try:
        invoke_url = _normalise_https_url(binding.get("invoke_url"))
        normalised_audience = _normalise_https_url(audience)
    except RuntimeBindingError:
        return
    if normalised_audience != invoke_url:
        problems.append(f"{label}.auth.audience must equal {label}.invoke_url")
    service_account = auth.get("invoker_service_account")
    if not isinstance(service_account, str) or not _SERVICE_ACCOUNT_PATTERN.fullmatch(
        service_account
    ):
        problems.append(
            f"{label}.auth.invoker_service_account must be a Google service account"
        )


def _validate_lambda_binding(
    binding: Mapping[str, Any], label: str, problems: list[str]
) -> None:
    resource = binding.get("resource")
    if not isinstance(resource, str) or not _AWS_LAMBDA_ARN_PATTERN.fullmatch(resource):
        problems.append(
            f"{label}.resource must be an AWS Lambda function ARN for aws-lambda"
        )
    auth = binding.get("auth")
    if not isinstance(auth, dict):
        return
    if auth.get("type") != "aws-lambda-invoke":
        problems.append(f"{label}.auth.type must be 'aws-lambda-invoke' for aws-lambda")
        return
    _validate_application_secret_header(auth, label, problems)


def _validate_http_secret_binding(
    binding: Mapping[str, Any],
    label: str,
    problems: list[str],
    *,
    resource_pattern: re.Pattern[str],
    provider: str,
    require_path_prefix: bool = False,
) -> None:
    resource = binding.get("resource")
    if not isinstance(resource, str) or not resource_pattern.fullmatch(resource):
        problems.append(
            f"{label}.resource has an invalid provider identity for {provider}"
        )
    auth = binding.get("auth")
    if not isinstance(auth, dict):
        return
    if auth.get("type") != "http-header-secret":
        problems.append(f"{label}.auth.type must be 'http-header-secret' for {provider}")
        return
    _validate_application_secret_header(auth, label, problems)
    if require_path_prefix:
        _validate_invoke_path_prefix(auth, label, problems)


def _validate_application_secret_header(
    auth: Mapping[str, Any], label: str, problems: list[str]
) -> None:
    parameters = auth.get("parameters")
    if not isinstance(parameters, Mapping):
        problems.append(
            f"{label}.auth.parameters.application_secret_header is required"
        )
        return
    header = parameters.get("application_secret_header")
    if not isinstance(header, str) or _APPLICATION_SECRET_HEADER_PATTERN.fullmatch(header) is None:
        problems.append(
            f"{label}.auth.parameters.application_secret_header must be a safe HTTP header name"
        )


def _validate_invoke_path_prefix(
    auth: Mapping[str, Any], label: str, problems: list[str]
) -> None:
    parameters = auth.get("parameters")
    if not isinstance(parameters, Mapping):
        return
    prefix = parameters.get("invoke_path_prefix")
    if not isinstance(prefix, str) or _INVOKE_PATH_PREFIX_PATTERN.fullmatch(prefix) is None:
        problems.append(
            f"{label}.auth.parameters.invoke_path_prefix must be a safe absolute path prefix"
        )


def _validate_auth(value: Any, label: str, problems: list[str]) -> None:
    if not isinstance(value, dict):
        problems.append(f"{label}.auth must be an object")
        return
    _unknown_fields(
        value,
        {
            "type",
            "audience",
            "principal",
            "credential_ref",
            "invoker_service_account",
            "parameters",
        },
        f"{label}.auth",
        problems,
    )
    if not isinstance(value.get("type"), str) or not value["type"].strip():
        problems.append(f"{label}.auth.type must be a non-empty string")
    if "audience" in value:
        try:
            _normalise_https_url(value["audience"])
        except RuntimeBindingError as exc:
            problems.append(f"{label}.auth.audience {exc}")
    if "principal" in value and (
        not isinstance(value["principal"], str) or not value["principal"].strip()
    ):
        problems.append(f"{label}.auth.principal must be a non-empty string when present")
    if "credential_ref" in value and (
        not isinstance(value["credential_ref"], str)
        or not value["credential_ref"].strip()
    ):
        problems.append(
            f"{label}.auth.credential_ref must be a non-empty host-local reference when present"
        )
    if "parameters" in value and not isinstance(value["parameters"], dict):
        problems.append(f"{label}.auth.parameters must be an object when present")


def _normalise_https_url(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeBindingError("must be a non-empty HTTPS base URL")
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeBindingError(
            "must be an HTTPS base URL without path, query, fragment, or credentials"
        )
    return f"https://{parsed.netloc}"


def _string_list(value: Any, label: str, problems: list[str]) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        problems.append(f"{label} must be a list of non-empty strings")
        return
    if len(set(value)) != len(value):
        problems.append(f"{label} must not contain duplicate capabilities")


def _unknown_fields(
    value: Mapping[str, Any], allowed: set[str], label: str, problems: list[str]
) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        problems.append(f"{label} has unknown fields {unknown}")
