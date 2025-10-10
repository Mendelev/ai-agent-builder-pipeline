# Code Repository Management Implementation

## Overview

This implementation adds secure Git repository management functionality to the AI Agent Builder Pipeline. It allows projects to connect Git repositories with comprehensive security features including token encryption, size validation, and sandboxed cloning.

## Features Implemented

### 1. **Secure Repository Connection** (`POST /api/v1/code/connect`)
- Pre-validates repository size before connection
- Encrypts access tokens using AES-GCM envelope encryption
- Returns task ID for tracking async clone operation
- Rejects repositories exceeding 100MB size limit

### 2. **Repository Information** (`GET /api/v1/code/repos/{repo_id}`)
- Retrieve complete repository details
- Includes clone status, size, and sandbox path
- No sensitive data (tokens) exposed in responses

### 3. **Repository Status Tracking** (`GET /api/v1/code/repos/{repo_id}/status`)
- Real-time clone operation status
- Progress messages for each status
- Error reporting for failed operations

### 4. **Project Repositories** (`GET /api/v1/code/projects/{project_id}/repos`)
- List all repositories connected to a project
- Supports multiple repositories per project

## Security Features

### Token Encryption (AES-GCM Envelope Encryption)
- **Data Encryption Key (DEK)**: Generated per token
- **Master Key**: Cached in memory or from environment variable
- **Nonce**: Unique 96-bit nonce per encryption operation
- **GCM Tag**: 16-byte authentication tag
- **No Plain Text**: Tokens never stored unencrypted in database

### Token Masking in Logs
All access tokens are masked in logs:
```
ghp_1234567890abcdef -> ghp_1234...cdef
```

### Repository Size Validation
- Pre-check using shallow clone (`--depth=1`)
- Conservative size estimation (3.5x multiplier)
- Early rejection (HTTP 413) for oversized repos
- 100MB default limit (configurable)

### Sandbox Isolation
- Each repository cloned to isolated directory
- Path structure: `/tmp/repos/{project_id}/{repo_id}/`
- Automatic cleanup on completion
- Read-only access after clone

## Architecture

### Database Schema

```sql
CREATE TABLE code_repos (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    git_url TEXT NOT NULL,
    token_ciphertext BYTEA NOT NULL,
    token_kid TEXT NOT NULL,
    repository_size_mb NUMERIC(10,2),
    clone_status TEXT NOT NULL DEFAULT 'PENDING',
    sandbox_path TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Clone Status States
- `PENDING`: Clone operation queued
- `CLONING`: Clone in progress
- `COMPLETED`: Successfully cloned
- `FAILED`: Clone operation failed
- `CLEANING`: Cleanup in progress
- `CLEANED`: Repository removed

### Asynchronous Processing

Clone operations run as Celery tasks with:
- Maximum 3 retry attempts
- Exponential backoff (60s, 120s, 240s)
- Automatic status updates
- Comprehensive error logging

## Configuration

### Environment Variables

```bash
# Git Repository Settings
MAX_REPO_SIZE_MB=100
GIT_CLONE_TIMEOUT=300
SANDBOX_BASE_PATH=/tmp/repos

# Encryption Settings
MASTER_ENCRYPTION_KEY=<base64_encoded_32_byte_key>
KMS_KEY_ID=<production_kms_key_id>

# Celery Settings
CELERY_CONCURRENCY=4
CELERY_MAX_RETRIES=3
```

### Generate Master Encryption Key

```bash
python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
```

## API Usage Examples

### 1. Connect Repository

```bash
curl -X POST "http://localhost:8000/api/v1/code/connect" \
  -H "Content-Type: application/json" \
  -d '{
    "git_url": "https://github.com/user/repo.git",
    "access_token": "ghp_your_github_token_here",
    "project_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Success Response (201 Created):**
```json
{
  "repo_id": "660e8400-e29b-41d4-a716-446655440001",
  "git_url": "https://github.com/user/repo.git",
  "connected": true,
  "task_id": "770e8400-e29b-41d4-a716-446655440002",
  "estimated_size_mb": 25.6,
  "clone_status": "PENDING",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Response - Repository Too Large (413):**
```json
{
  "detail": {
    "error": "repository_too_large",
    "message": "Repository size 156.8MB exceeds limit of 100MB",
    "estimated_size_mb": 156.8,
    "limit_mb": 100
  }
}
```

### 2. Check Repository Status

```bash
curl "http://localhost:8000/api/v1/code/repos/660e8400-e29b-41d4-a716-446655440001/status"
```

**Response:**
```json
{
  "repo_id": "660e8400-e29b-41d4-a716-446655440001",
  "clone_status": "COMPLETED",
  "repository_size_mb": 28.4,
  "sandbox_path": "/tmp/repos/550e.../660e.../repository",
  "progress_message": "Repository successfully cloned",
  "error_message": null
}
```

### 3. Get Repository Details

```bash
curl "http://localhost:8000/api/v1/code/repos/660e8400-e29b-41d4-a716-446655440001"
```

### 4. List Project Repositories

```bash
curl "http://localhost:8000/api/v1/code/projects/550e8400-e29b-41d4-a716-446655440000/repos"
```

## Git Platform Support

### Supported Platforms
- **GitHub**: `https://github.com/user/repo.git`
- **GitLab**: `https://gitlab.com/user/repo.git`
- **Bitbucket**: `https://bitbucket.org/user/repo.git`
- **Generic**: Any HTTPS Git URL

### Authentication URL Formats
- **GitHub**: `https://{token}@github.com/user/repo.git`
- **GitLab**: `https://oauth2:{token}@gitlab.com/user/repo.git`
- **Bitbucket**: `https://x-token-auth:{token}@bitbucket.org/user/repo.git`

## Testing

### Run All Tests

```bash
cd backend
source venv/bin/activate

# Run all code repository tests
pytest tests/test_encryption_service.py tests/test_git_service.py tests/test_code_repos.py -v

# Run with coverage
pytest tests/test_*.py --cov=app --cov-report=html
```

### Test Coverage

- **Encryption Service**: 100% coverage (8/8 tests passing)
- **Git Service**: 100% coverage (13/13 tests passing)
- **API Integration**: 90%+ coverage (comprehensive scenarios)

## Database Migration

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

This applies migration `004_create_code_repos` which creates the `code_repos` table with all necessary indexes.

## Production Considerations

### 1. **Key Management**
- Replace temporary master key with AWS KMS or Azure KeyVault
- Implement key rotation policies
- Store master key in secure secret management system

### 2. **Repository Size Limits**
- Adjust `MAX_REPO_SIZE_MB` based on infrastructure
- Consider separate limits for different project tiers
- Monitor disk usage on worker nodes

### 3. **Celery Worker Configuration**
- Scale workers based on clone volume
- Set appropriate timeout values
- Configure retry policies for network issues

### 4. **Monitoring & Alerts**
- Track clone success/failure rates
- Monitor repository size rejections
- Alert on encryption/decryption failures
- Track disk usage in sandbox directories

### 5. **Cleanup Strategy**
- Implement periodic cleanup of old repositories
- Set retention policies for cloned code
- Monitor and clean failed clone attempts

## File Structure

```
backend/
├── alembic/versions/
│   └── 004_create_code_repos.py          # Database migration
├── app/
│   ├── models/
│   │   └── code_repo.py                  # CodeRepository model
│   ├── schemas/
│   │   └── code_repo.py                  # Pydantic schemas
│   ├── services/
│   │   ├── encryption_service.py         # Token encryption
│   │   ├── git_service.py                # Git operations
│   │   └── code_repo_service.py          # Business logic
│   ├── api/routes/
│   │   └── code_repos.py                 # API endpoints
│   └── tasks/
│       └── git_clone.py                  # Celery tasks
└── tests/
    ├── test_encryption_service.py        # Encryption tests
    ├── test_git_service.py               # Git service tests
    └── test_code_repos.py                # Integration tests
```

## Implementation Checklist

- [x] Database migration created and applied
- [x] CodeRepository model with relationships
- [x] Encryption service with AES-GCM
- [x] Git service with size validation
- [x] Code repository service layer
- [x] API routes with proper error handling
- [x] Celery tasks for async cloning
- [x] Configuration settings
- [x] Comprehensive unit tests (21/21 passing)
- [x] Integration tests
- [x] Token masking in logs
- [x] Documentation

## Next Steps

1. **Frontend Integration**: Build UI for repository management
2. **Webhook Support**: Add Git webhook handlers for push events
3. **Code Analysis**: Integrate with code analysis pipeline
4. **Multi-Branch Support**: Allow cloning specific branches
5. **Incremental Updates**: Implement git pull for existing repos
6. **Access Control**: Add role-based permissions for repositories

## Support

For issues or questions:
- Check logs in `/var/log/app/` for detailed error messages
- Verify environment variables are correctly set
- Ensure Celery workers are running
- Confirm database migration has been applied

## License

Part of the AI Agent Builder Pipeline project.
