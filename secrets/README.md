# Secrets folder

Put the GitHub App private key here as `github-app.pem`. Everything in this
folder except this README is git-ignored, so the key is never committed.

Docker Compose mounts this folder read-only at `/run/secrets` in the `api` and
`worker` containers.

How to get the key: GitHub > Settings > Developer settings > GitHub Apps >
your app > General > Private keys > **Generate a private key**. GitHub downloads
a `.pem` file once; rename it to `github-app.pem` and move it here.
