# Artifact result layout (normative)

Run artifacts are separate from the .apm package. The package contains source
inputs and declarations; a result points to immutable output artifacts.

The logical result layout is:

    <result-root>/
      result.json
      artifacts/
        <artifact-name>/<relative-file>

Each result artifact path MUST be relative, use POSIX separators, begin with
artifacts/, and contain neither an absolute component nor .. . Its logical name
MUST match a package declaration. A runner MUST NOT report undeclared output as
a successful declared artifact.

Each artifact entry MUST contain name, path, media_type, size_bytes, and sha256.
size_bytes is the exact byte length and sha256 is the SHA-256 of those bytes.
Consumers MUST verify the digest before trusting an artifact. A locator such as
an object-store key MAY be added, but it cannot replace the logical path or
digest.

The optional manifest declarations are:

    artifacts:
      declared:
        - name: greeting
          path: artifacts/greeting/greeting.md
          media_type: text/markdown
    fixtures:
      declared:
        - name: hello
          path: fixtures/hello-input.json
          media_type: application/json

Fixture paths are package-relative, read-only test inputs. They are not result
artifacts and MUST NOT be exposed as generated output.
