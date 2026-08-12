# Permissions (normative)

Capabilities describe services a package needs. Permissions describe what the
package and caller are allowed to do. A capability is not permission.

The optional declaration is:

    permissions:
      requires:
        scopes: [artifact:write]

Scope names are host-defined strings registered by the host. A public package
MUST use documented scopes only and MUST NOT embed credentials, bearer tokens,
tenant identifiers, or provider secrets in source or manifest.

Before runner selection, the host computes:

    missing = package_required_scopes - caller_effective_scopes

Any missing scope is a hard rejection. The host MUST fail closed and MUST NOT
silently drop a requested scope, substitute a broader scope, or use visibility
as authorization. An absent permissions declaration means no additional
declared requirement; it does not grant access.

The host MUST still apply least privilege to filesystem, network, process,
secret, and artifact access. Permission decisions happen before package code
runs and may be represented in diagnostic metadata without secret values.
