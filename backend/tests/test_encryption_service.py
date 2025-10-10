import pytest
from uuid import uuid4
from app.services.encryption_service import EncryptionService


class TestEncryptionService:
    """Test cases for encryption service"""
    
    def test_encrypt_decrypt_token(self):
        """Test token encryption and decryption cycle"""
        service = EncryptionService()
        original_token = "ghp_test_token_1234567890"
        project_id = str(uuid4())
        
        # Encrypt token
        ciphertext, key_id = service.encrypt_token(original_token, project_id)
        
        assert isinstance(ciphertext, bytes)
        assert len(ciphertext) > len(original_token)
        assert key_id.startswith('key-')
        
        # Decrypt token
        decrypted_token = service.decrypt_token(ciphertext, key_id, project_id)
        
        assert decrypted_token == original_token
    
    def test_encrypt_different_tokens_produce_different_ciphertext(self):
        """Test that different tokens produce different ciphertext"""
        service = EncryptionService()
        project_id = str(uuid4())
        
        token1 = "ghp_token_1234567890"
        token2 = "ghp_token_0987654321"
        
        ciphertext1, key_id1 = service.encrypt_token(token1, project_id)
        ciphertext2, key_id2 = service.encrypt_token(token2, project_id)
        
        assert ciphertext1 != ciphertext2
        assert key_id1 != key_id2
    
    def test_encrypt_same_token_twice_produces_different_ciphertext(self):
        """Test that encrypting the same token twice produces different ciphertext (due to different nonces)"""
        service = EncryptionService()
        project_id = str(uuid4())
        token = "ghp_test_token_1234567890"
        
        ciphertext1, key_id1 = service.encrypt_token(token, project_id)
        ciphertext2, key_id2 = service.encrypt_token(token, project_id)
        
        # Different ciphertext due to different nonces
        assert ciphertext1 != ciphertext2
        assert key_id1 != key_id2
        
        # But both should decrypt to the same token
        decrypted1 = service.decrypt_token(ciphertext1, key_id1, project_id)
        decrypted2 = service.decrypt_token(ciphertext2, key_id2, project_id)
        
        assert decrypted1 == token
        assert decrypted2 == token
    
    def test_decrypt_with_wrong_key_fails(self):
        """Test that decryption with wrong key fails"""
        service = EncryptionService()
        project_id = str(uuid4())
        token = "ghp_test_token_1234567890"
        
        ciphertext, key_id = service.encrypt_token(token, project_id)
        
        # Try to decrypt with wrong key (corrupted ciphertext)
        corrupted_ciphertext = b'x' + ciphertext[1:]
        
        with pytest.raises(Exception):
            service.decrypt_token(corrupted_ciphertext, key_id, project_id)
    
    def test_mask_token(self):
        """Test token masking for logs"""
        # Test normal token
        token = "ghp_1234567890abcdef"
        masked = EncryptionService.mask_token(token)
        assert masked == "ghp_...cdef"
        
        # Test short token
        short_token = "abc"
        masked_short = EncryptionService.mask_token(short_token)
        assert masked_short == "***"
        
        # Test very long token
        long_token = "ghp_" + "a" * 100
        masked_long = EncryptionService.mask_token(long_token)
        assert masked_long.startswith("ghp_")
        assert masked_long.endswith("aaaa")
        assert "..." in masked_long
    
    def test_encrypt_empty_string(self):
        """Test encryption of empty string"""
        service = EncryptionService()
        project_id = str(uuid4())
        
        # Empty string should still be encrypted
        ciphertext, key_id = service.encrypt_token("", project_id)
        
        assert isinstance(ciphertext, bytes)
        assert len(ciphertext) > 0
        
        # Should decrypt back to empty string
        decrypted = service.decrypt_token(ciphertext, key_id, project_id)
        assert decrypted == ""
    
    def test_encrypt_special_characters(self):
        """Test encryption of tokens with special characters"""
        service = EncryptionService()
        project_id = str(uuid4())
        
        special_token = "ghp_!@#$%^&*()_+-=[]{}|;':\",./<>?"
        
        ciphertext, key_id = service.encrypt_token(special_token, project_id)
        decrypted = service.decrypt_token(ciphertext, key_id, project_id)
        
        assert decrypted == special_token
    
    def test_encrypt_unicode_characters(self):
        """Test encryption of tokens with unicode characters"""
        service = EncryptionService()
        project_id = str(uuid4())
        
        unicode_token = "ghp_测试_🔐_token"
        
        ciphertext, key_id = service.encrypt_token(unicode_token, project_id)
        decrypted = service.decrypt_token(ciphertext, key_id, project_id)
        
        assert decrypted == unicode_token
