# gateway/encryption_logic.py
from ff3 import FF3Cipher

class GatewayProtector:
    def __init__(self, key: str, tweak: str):
        """
        Initializes the FPE Cipher.
        Key: 128-bit hex key
        Tweak: 56-bit hex tweak
        """
        self.key = key
        self.tweak = tweak
        # Using radix 10 for numeric phone numbers/account IDs
        self.cipher = FF3Cipher.withCustomAlphabet(self.key, self.tweak, "0123456789")

    def encrypt_identifier(self, raw_id: str):
        """
        Encrypts a phone number or account ID while preserving format.
        Example: '0722123456' -> '0722984102'
        """
        # We often keep the prefix (0722) and encrypt the rest
        prefix = raw_id[:4]
        suffix = raw_id[4:]
        
        encrypted_suffix = self.cipher.encrypt(suffix)
        return f"{prefix}{encrypted_suffix}"

    def decrypt_identifier(self, encrypted_id: str):
        """
        Decrypts for authorized administrative auditing.
        """
        prefix = encrypted_id[:4]
        suffix = encrypted_id[4:]
        
        decrypted_suffix = self.cipher.decrypt(suffix)
        return f"{prefix}{decrypted_suffix}"

# Sample Usage for Sharon's testing:
if __name__ == "__main__":
    # In production, move these to your .env file!
    KEY = "EF4359D8D580AA4F7F036D6F04FC6A94" 
    TWEAK = "D8E792"
    
    protector = GatewayProtector(KEY, TWEAK)
    test_phone = "0722123456"
    
    masked = protector.encrypt_identifier(test_phone)
    print(f"Original: {test_phone}")
    print(f"Masked:   {masked}") # AI sees this, privacy is maintained.