import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Tuple, Optional
import uuid
from app.core.logging_config import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class EncryptionService:
    """Service for encrypting/decrypting sensitive data using AES-GCM envelope encryption"""
    
    def __init__(self):
        self.key_size = 32  # 256 bits for AES-256
        self.nonce_size = 12  # 96 bits for GCM
        self._master_key = None  # Cache master key
    
    def generate_data_key(self) -> bytes:
        """Generate a random data encryption key"""
        return os.urandom(self.key_size)
    
    def encrypt_token(self, plaintext_token: str, project_id: Optional[str] = None) -> Tuple[bytes, str]:
        """
        Encrypt access token using AES-GCM envelope encryption
        
        Args:
            plaintext_token: The token to encrypt
            project_id: Optional project ID for logging context
            
        Returns:
            Tuple of (ciphertext, key_id)
        """
        try:
            # Generate a unique data encryption key for this token
            dek = self.generate_data_key()
            
            # Generate unique nonce
            nonce = os.urandom(self.nonce_size)
            
            # Encrypt the token with the DEK
            aesgcm = AESGCM(dek)
            token_ciphertext = aesgcm.encrypt(nonce, plaintext_token.encode('utf-8'), None)
            
            # In production, this would encrypt DEK with KMS/KeyVault
            # For now, we'll simulate this with a master key approach
            encrypted_dek = self._encrypt_dek_with_master_key(dek)
            
            # Create the final ciphertext (nonce + encrypted_token + encrypted_dek)
            final_ciphertext = nonce + token_ciphertext + encrypted_dek
            
            # Generate a key ID to track this encryption
            key_id = f"key-{uuid.uuid4().hex[:16]}"
            
            logger.info(
                "Token encrypted successfully",
                extra={
                    "project_id": project_id,
                    "key_id": key_id,
                    "token_length": len(plaintext_token),
                    "ciphertext_length": len(final_ciphertext)
                }
            )
            
            return final_ciphertext, key_id
            
        except Exception as e:
            logger.error(
                "Token encryption failed",
                extra={
                    "project_id": project_id,
                    "error": str(e)
                }
            )
            raise
    
    def decrypt_token(self, ciphertext: bytes, key_id: str, project_id: Optional[str] = None) -> str:
        """
        Decrypt access token using AES-GCM envelope decryption
        
        Args:
            ciphertext: The encrypted token data
            key_id: The key identifier used for encryption
            project_id: Optional project ID for logging context
            
        Returns:
            Decrypted plaintext token
        """
        try:
            # The encrypted DEK size is nonce (12) + DEK (32) + GCM tag (16) = 60 bytes
            encrypted_dek_size = self.nonce_size + self.key_size + 16
            
            # Extract components from ciphertext
            nonce = ciphertext[:self.nonce_size]
            encrypted_dek = ciphertext[-encrypted_dek_size:]  # Last 60 bytes
            token_ciphertext = ciphertext[self.nonce_size:-encrypted_dek_size]  # Middle part
            
            # Decrypt the DEK with master key
            dek = self._decrypt_dek_with_master_key(encrypted_dek)
            
            # Decrypt the token with the DEK
            aesgcm = AESGCM(dek)
            plaintext_token = aesgcm.decrypt(nonce, token_ciphertext, None)
            
            logger.info(
                "Token decrypted successfully",
                extra={
                    "project_id": project_id,
                    "key_id": key_id,
                    "token_length": len(plaintext_token)
                }
            )
            
            return plaintext_token.decode('utf-8')
            
        except Exception as e:
            logger.error(
                "Token decryption failed",
                extra={
                    "project_id": project_id,
                    "key_id": key_id,
                    "error": str(e)
                }
            )
            raise
    
    def _get_master_key(self) -> bytes:
        """Get or generate master key - in production this would be from KMS/KeyVault"""
        # Return cached key if available
        if self._master_key is not None:
            return self._master_key
            
        # Use settings from Pydantic (which loads from .env)
        master_key_b64 = settings.MASTER_ENCRYPTION_KEY
        if master_key_b64:
            self._master_key = base64.b64decode(master_key_b64)
            logger.info("Loaded master encryption key from settings")
            return self._master_key
        
        # Generate a master key if none exists (NOT for production)
        self._master_key = os.urandom(self.key_size)
        logger.warning(
            "Generated temporary master key - NOT suitable for production",
            extra={"key_b64": base64.b64encode(self._master_key).decode()}
        )
        return self._master_key
    
    def _encrypt_dek_with_master_key(self, dek: bytes) -> bytes:
        """Encrypt DEK with master key (simulates KMS operation)"""
        master_key = self._get_master_key()
        nonce = os.urandom(self.nonce_size)
        aesgcm = AESGCM(master_key)
        return nonce + aesgcm.encrypt(nonce, dek, None)
    
    def _decrypt_dek_with_master_key(self, encrypted_dek: bytes) -> bytes:
        """Decrypt DEK with master key (simulates KMS operation)"""
        master_key = self._get_master_key()
        nonce = encrypted_dek[:self.nonce_size]
        ciphertext = encrypted_dek[self.nonce_size:]
        aesgcm = AESGCM(master_key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    
    @staticmethod
    def mask_token(token: str) -> str:
        """Mask token for logging purposes"""
        if len(token) <= 8:
            return "***"
        return f"{token[:4]}...{token[-4:]}"
