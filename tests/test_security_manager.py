# tests/test_security_manager.py
import pytest
from unittest.mock import patch, mock_open, MagicMock
from hipaa_training.security import SecurityManager
import base64


@pytest.fixture
def security_manager():
    """Create security manager with test environment"""
    with patch.dict('os.environ', {
        'HIPAA_ENCRYPTION_KEY': 'test-key-for-testing-only-32-chars',
        'HIPAA_SALT': 'a1b2c3d4e5f6g7h8'
    }):
        # Mock the database connection in log_action
        with patch('sqlite3.connect'):
            manager = SecurityManager()
            return manager


def test_encrypt_decrypt_round_trip(security_manager):
    """Test that encryption and decryption work correctly"""
    original_data = "Sensitive HIPAA compliance data"
    
    encrypted = security_manager.encrypt_data(original_data)
    decrypted = security_manager.decrypt_data(encrypted)
    
    assert decrypted == original_data
    assert encrypted != original_data
    assert isinstance(encrypted, str)


def test_encrypt_empty_string(security_manager):
    """Test encryption handles empty strings"""
    result = security_manager.encrypt_data("")
    assert result == ""


def test_decrypt_empty_string(security_manager):
    """Test decryption handles empty strings"""
    result = security_manager.decrypt_data("")
    assert result == ""


def test_encrypt_none(security_manager):
    """Test encryption handles None values"""
    result = security_manager.encrypt_data(None)
    assert result is None


def test_log_action(security_manager):
    """Test audit logging functionality"""
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        
        security_manager.log_action(123, "TEST_ACTION", "Test details for audit")
        
        # Verify database insert was called
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "INSERT INTO audit_log" in call_args[0]


def test_encryption_with_special_characters(security_manager):
    """Test encryption handles special characters"""
    test_data = 'Special chars: ñáéíóú 测试 🚀'
    encrypted = security_manager.encrypt_data(test_data)
    decrypted = security_manager.decrypt_data(encrypted)
    assert decrypted == test_data


def test_encryption_with_long_text(security_manager):
    """Test encryption handles long text"""
    long_text = "A" * 10000  # 10k characters
    encrypted = security_manager.encrypt_data(long_text)
    decrypted = security_manager.decrypt_data(encrypted)
    assert decrypted == long_text
    assert len(encrypted) > len(long_text)  # Encrypted data is larger


def test_encrypt_file(security_manager, tmp_path):
    """Test file encryption with chunked approach"""
    # Create a temporary test file
    test_file = tmp_path / "test_input.txt"
    test_file.write_text("Test content for file encryption")
    
    output_file = tmp_path / "test_output.enc"
    
    # Encrypt the file
    security_manager.encrypt_file(str(test_file), str(output_file))
    
    # Verify output file exists and is not empty
    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_decrypt_file(security_manager, tmp_path):
    """Test file decryption"""
    # Create and encrypt a file
    original_content = "Secret HIPAA data for testing"
    test_file = tmp_path / "original.txt"
    test_file.write_text(original_content)
    
    encrypted_file = tmp_path / "encrypted.enc"
    decrypted_file = tmp_path / "decrypted.txt"
    
    # Encrypt then decrypt
    security_manager.encrypt_file(str(test_file), str(encrypted_file))
    security_manager.decrypt_file(str(encrypted_file), str(decrypted_file))
    
    # Verify content matches
    assert decrypted_file.read_text() == original_content


def test_get_client_ip(security_manager):
    """Test client IP retrieval"""
    with patch.dict('os.environ', {'CLIENT_IP': '192.168.1.100'}):
        ip = security_manager._get_client_ip()
        assert ip == '192.168.1.100'
    
    # Test default
    with patch.dict('os.environ', {}, clear=True):
        ip = security_manager._get_client_ip()
        assert ip == '127.0.0.1'
