# Release Workflow Testing Guide

This document provides instructions for testing the automated release workflow.

## Prerequisites

Before testing the release workflow, ensure:

1. **GitHub Secrets are configured**:
   - `DOCKERHUB_USERNAME`: Set to `rdxmaster` (or your Docker Hub username)
   - `DOCKERHUB_TOKEN`: Docker Hub access token with read/write permissions

2. **Repository permissions**:
   - Write access to the repository
   - Permission to create tags
   - Permission to trigger GitHub Actions

## Setting Up Docker Hub Token

If the secrets are not yet configured:

1. Log in to [Docker Hub](https://hub.docker.com/)
2. Go to **Account Settings** → **Security**
3. Click **New Access Token**
4. Configure the token:
   - **Description**: `GitHub Actions Release`
   - **Access permissions**: Read & Write
5. Copy the generated token
6. Add to GitHub:
   - Go to repository **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `DOCKERHUB_TOKEN`
   - Value: Paste the token
   - Click **Add secret**

## Version Tag Behavior

The workflow automatically detects version types:

- **Stable releases** (e.g., `v1.0.0`, `v2.1.3`):
  - Tagged with version number AND `latest` on Docker Hub
  - Created as regular GitHub releases
  - Example: `rdxmaster/easy-net-visibility-server-django:1.0.0` and `rdxmaster/easy-net-visibility-server-django:latest`

- **Pre-releases** (e.g., `v0.0.1-test`, `v1.0.0-alpha`, `v2.0.0-rc1`):
  - Tagged with version number ONLY (does NOT update `latest`)
  - Created as pre-release on GitHub
  - Prevents test versions from affecting production users
  - Example: Only `rdxmaster/easy-net-visibility-server-django:0.0.1-test` is created

**Note:** Any version containing a hyphen followed by letters (e.g., `-test`, `-alpha`, `-beta`, `-rc`) is treated as a pre-release.

## Manual Testing (Recommended First Test)

The safest way to test is using the manual workflow dispatch:

1. Navigate to the [Actions tab](https://github.com/rdar-lab/easyNetVisibility/actions)
2. Select the **Release** workflow from the left sidebar
3. Click **Run workflow** button (on the right)
4. Enter a test version tag: `v0.0.1-test`
5. Click **Run workflow** to start

### What to Expect

The workflow will:
1. Build Docker images for server and sensor from the specified tag
2. Push images to Docker Hub with tags:
   - `rdxmaster/easy-net-visibility-server-django:0.0.1-test`
   - `rdxmaster/easy-net-visibility-sensor:0.0.1-test`
   - **Note:** Pre-release versions (containing `-test`, `-alpha`, `-beta`, `-rc`) will NOT update the `latest` tag
3. Create a GitHub Release for tag `v0.0.1-test` marked as pre-release

### Verify the Results

1. **Check GitHub Actions**:
   - Workflow should complete successfully (green checkmark)
   - Review logs for any errors

2. **Check GitHub Releases**:
   - Go to [Releases](https://github.com/rdar-lab/easyNetVisibility/releases)
   - Verify `v0.0.1-test` release exists
   - Confirm it's marked as "Pre-release"
   - Check release notes are generated

3. **Check Docker Hub**:
   - Server: https://hub.docker.com/r/rdxmaster/easy-net-visibility-server-django/tags
   - Sensor: https://hub.docker.com/r/rdxmaster/easy-net-visibility-sensor/tags
   - Verify `0.0.1-test` tag exists
   - Confirm `latest` tag was NOT updated (points to previous stable release)

4. **Test Docker Images**:
   ```bash
   # Pull and test server image
   docker pull rdxmaster/easy-net-visibility-server-django:0.0.1-test
   docker run --rm rdxmaster/easy-net-visibility-server-django:0.0.1-test python --version

   # Pull and test sensor image
   docker pull rdxmaster/easy-net-visibility-sensor:0.0.1-test
   docker run --rm rdxmaster/easy-net-visibility-sensor:0.0.1-test --help
   ```

## Testing with Git Tags

Once manual testing is successful, test the automatic trigger:

1. **Create and push a test tag**:
   ```bash
   git tag -a v0.0.2-test -m "Test release v0.0.2"
   git push origin v0.0.2-test
   ```

2. **Monitor the workflow**:
   - Go to [Actions tab](https://github.com/rdar-lab/easyNetVisibility/actions)
   - Workflow should start automatically
   - Wait for completion

3. **Verify results** (same as manual testing):
   - Check GitHub Release for `v0.0.2-test`
   - Check Docker Hub for `0.0.2-test` tags
   - Test pulling and running images

## Creating a Real Release

Once testing is complete and successful:

1. **Clean up test releases** (optional):
   ```bash
   # Delete test tags
   git tag -d v0.0.1-test v0.0.2-test
   git push origin :refs/tags/v0.0.1-test
   git push origin :refs/tags/v0.0.2-test
   ```

2. **Create a real release**:
   ```bash
   # Ensure you're on the main branch with latest changes
   git checkout main
   git pull

   # Create a proper release tag
   git tag -a v1.0.0 -m "Release version 1.0.0

   Initial production release with:
   - Server (Django-based web dashboard)
   - Sensor (Network scanning agent)
   - Automated release workflow"

   # Push the tag
   git push origin v1.0.0
   ```

3. **Monitor and verify**:
   - Check workflow completion
   - Verify GitHub Release
   - Verify Docker Hub images
   - Update README if needed

## Troubleshooting

### Workflow Fails on Docker Login

**Error**: `Error: Username and password required`

**Solution**: Verify GitHub secrets are set correctly:
- `DOCKERHUB_USERNAME` should be `rdxmaster`
- `DOCKERHUB_TOKEN` should be a valid Docker Hub access token (not password)

### Workflow Fails on Docker Push

**Error**: `denied: requested access to the resource is denied`

**Solution**:
- Verify Docker Hub token has read/write permissions
- Verify the username has push access to the repositories
- Check token hasn't expired

### Docker Build Fails

**Error**: Build errors in Dockerfile

**Solution**:
- Test building locally first:
  ```bash
  cd easyNetVisibility/server/server_django
  docker build -t test-server .

  cd ../../client
  docker build -t test-sensor .
  ```
- Fix any Dockerfile issues
- Commit and push fixes
- Retry the workflow

### Release Already Exists

**Error**: `Release already exists`

**Solution**:
- Delete the existing release on GitHub
- Delete the tag: `git push origin :refs/tags/vX.X.X`
- Recreate the tag and push again

## Cleanup

After testing, you may want to:

1. **Remove test releases** from GitHub Releases page
2. **Remove test tags** from Docker Hub (optional)
3. **Document any issues** encountered during testing

## Next Steps

After successful testing:

1. Update repository documentation with release information
2. Notify team members about the new release process
3. Consider setting up automated testing before releases
4. Plan regular release cadence (e.g., monthly, quarterly)
