# EV-02 — Official Git transport attempts

Scope was limited to `https://github.com/princeton-nlp/WebShop.git`.

## Attempt 1 — clone

```bash
git clone --filter=blob:none --no-checkout https://github.com/princeton-nlp/WebShop.git local_sources/third_party/webshop
```

Exit code: `128`

```text
Cloning into 'local_sources/third_party/webshop'...
fatal: unable to access 'https://github.com/princeton-nlp/WebShop.git/': GnuTLS recv error (-110): The TLS connection was non-properly terminated.
```

No checkout directory remained after this failed clone.

## Attempt 2 — empty repository plus shallow commit fetch

```bash
git -C local_sources/third_party/webshop init
git -C local_sources/third_party/webshop remote add origin https://github.com/princeton-nlp/WebShop.git
git -C local_sources/third_party/webshop -c http.version=HTTP/1.1 fetch --depth=1 origin 64fa2a5
```

Fetch exit code: `128`

```text
fatal: unable to access 'https://github.com/princeton-nlp/WebShop.git/': GnuTLS recv error (-110): The TLS connection was non-properly terminated.
```

The local directory now contains only an empty `.git` repository with the official origin; no commit or worktree content was acquired.

## Attempt 3 — filtered no-tags fetch

```bash
git -C local_sources/third_party/webshop \
  -c http.version=HTTP/1.1 \
  -c http.lowSpeedLimit=1 \
  -c http.lowSpeedTime=300 \
  fetch --filter=blob:none --no-tags --depth=1 origin 64fa2a5
```

Exit code: `128`

```text
fatal: unable to access 'https://github.com/princeton-nlp/WebShop.git/': Failed to connect to github.com port 443 after 139402 ms: Couldn't connect to server
```

## Attempt 4 — lightweight official master lookup

```bash
git -c http.version=HTTP/1.1 ls-remote https://github.com/princeton-nlp/WebShop.git refs/heads/master
```

Result: command terminated after the controlled 60-second tool timeout.

```text
[codexpro] Command timed out after 60000 ms.
```

## Alternate local Git check

Windows PowerShell was reachable only through its absolute system path, but Windows Git was not installed or discoverable in the standard locations checked. No alternate Git client was available.

## Conclusion

The pinned commit could not be resolved or acquired because official Git transport was unavailable during execution. Per contract stop conditions, the Executor stopped before writing the checker/tests and did not select a mirror, fork, archive, different commit, GitHub API, or nonofficial endpoint.
