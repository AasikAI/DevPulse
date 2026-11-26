"""A throwaway RSA key pair for tests. Generated fresh each run; never a real credential."""

import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

PRIVATE_KEY_PEM = _private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode()

PUBLIC_KEY_PEM = (
    _private_key.public_key()
    .public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    .decode()
)

_directory = Path(tempfile.mkdtemp(prefix="devpulse-test-key-"))
PRIVATE_KEY_PATH = _directory / "github-app.pem"
PRIVATE_KEY_PATH.write_text(PRIVATE_KEY_PEM)

APP_ID = "424242"
APP_SLUG = "devpulse-test"
