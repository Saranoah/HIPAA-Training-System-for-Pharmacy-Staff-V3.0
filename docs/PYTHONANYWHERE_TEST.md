# PythonAnywhere Testing Checklist

## Pre-Deployment
- [ ] Create PythonAnywhere account (free tier is fine for testing)
- [ ] Note your username: ______________
- [ ] Verify Python 3.9+ available

## Deployment Steps
- [ ] Upload `deploy_package.zip` via Files tab
- [ ] Extract: `unzip deploy_package.zip`
- [ ] Navigate: `cd deploy_package`
- [ ] Install deps: `pip3.9 install --user -r requirements.txt`
- [ ] Generate encryption key: `python3.9 -c 'import secrets; print(secrets.token_urlsafe(32))'`
- [ ] Set in .env file
- [ ] Initialize: `python3.9 main.py --setup-only`

## Functional Tests
- [ ] Run environment check: `python3.9 scripts/check_environment.py`
- [ ] Run manual tests: `python3.9 scripts/manual_test.py`
- [ ] Start application: `python3.9 main.py`
- [ ] Create test user
- [ ] Complete one lesson
- [ ] Take mini quiz
- [ ] Complete full quiz (pass with 80%+)
- [ ] Verify certificate generated
- [ ] Complete checklist
- [ ] Generate CSV report
- [ ] Generate JSON report

## Performance Tests
- [ ] Measure startup time: `time python3.9 main.py --check-env`
- [ ] Test with 10 users created
- [ ] Generate report with 100+ records
- [ ] Check database file size
- [ ] Monitor memory usage: `top` or `htop`

## Security Tests
- [ ] Verify .env file permissions: `chmod 600 .env`
- [ ] Check database encryption
- [ ] Test audit logging
- [ ] Verify no passwords in logs
- [ ] Check file permissions on evidence folder

## Edge Cases
- [ ] Try creating duplicate username
- [ ] Try invalid role
- [ ] Try empty quiz answers
- [ ] Try uploading >5MB file (should fail)
- [ ] Try invalid file type for evidence

## Cleanup
- [ ] Remove test data: `rm -rf data/hipaa_training.db`
- [ ] Remove test reports: `rm -rf reports/*`
- [ ] Keep one clean instance for demo
