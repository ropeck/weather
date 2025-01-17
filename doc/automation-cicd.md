### CI/CD Automation for GitHub Repo with Kubernetes Deployment

This workflow automates the building and deployment of a Docker container whenever changes are pushed to the `master` branch. The container is built, pushed to Docker Hub, and deployed to a Kubernetes cluster.

#### Workflow File
Path: `.github/workflows/docker-build.yml`

#### Prerequisites
1. **GitHub Repository Secrets**:
   - `DOCKER_USERNAME`: Docker Hub username (`fogcat5`).
   - `DOCKER_PASSWORD`: Docker Hub personal access token (obtainable from the Docker Hub account page).
   - `GCP_SA_KEY`: Service account JSON key for Google Cloud Platform.

2. **Kubernetes Deployment**:
   Ensure that the Kubernetes deployment is set up to match the container image specified in the workflow.

#### Key Features
- **Docker Build and Push**: Automatically builds the Docker image and pushes it to Docker Hub with a `latest` tag and a commit-specific tag (`${{ github.sha }}`).
- **Google Kubernetes Engine (GKE) Integration**: Automatically applies the new container image to the Kubernetes pod and verifies the rollout.

---

#### Workflow Code
```yaml
name: Build and Deploy Docker Image

on:
  push:
    branches:
      - master

jobs:
  build-deploy:
    runs-on: ubuntu-latest

    steps:
      # Step 1: Checkout the repository code
      - name: Checkout code
        uses: actions/checkout@v3

      # Step 2: Set up Docker Buildx for multi-platform builds
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      # Step 3: Log in to Docker Hub
      - name: Log in to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      # Step 4: Build and push Docker image to Docker Hub
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            fogcat5/collector-webapp:latest
            fogcat5/collector-webapp:${{ github.sha }}

      # Step 5: Set up kubeconfig for Kubernetes authentication
      - name: Set up kubeconfig
        run: |
          echo "${{ secrets.KUBECONFIG_CONTENT }}" > kubeconfig
          export KUBECONFIG=$(pwd)/kubeconfig

      # Step 6: Authenticate to Google Kubernetes Engine (GKE)
      - name: Authenticate to GKE
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      # Step 7: Fetch GKE cluster credentials
      - name: Set up GKE
        uses: google-github-actions/get-gke-credentials@v1
        with:
          cluster_name: my-first-cluster
          location: us-west1-a
          project_id: k8s-project-441922

      # Step 8: Verify access to the Kubernetes cluster
      - name: Verify Kubernetes cluster access
        run: kubectl get nodes

      # Step 9: Deploy updated image to Kubernetes
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/collector-webapp collector-webapp=fogcat5/collector-webapp:${{ github.sha }}
          kubectl rollout status deployment/collector-webapp
```

---

### Suggestions for Improvement

1. **Security**:
   - Replace `DOCKER_PASSWORD` with an **encrypted token** if available.
   - Use a dedicated service account with limited permissions for the `GCP_SA_KEY`.

2. **Branch Management**:
   - Consider extending the workflow to include other branches (e.g., staging or feature branches) for testing before deployment to production.

3. **Testing Stage**:
   - Add a step to run automated tests (e.g., unit tests) before building the Docker image. For example:
     ```yaml
     - name: Run tests
       run: |
         python -m unittest discover tests/
     ```

4. **Rollbacks**:
   - Add a rollback mechanism in case the deployment fails. For example:
     ```yaml
     kubectl rollout undo deployment/collector-webapp
     ```

5. **Documentation Clarity**:
   - Explicitly state the deployment prerequisites, like the Kubernetes deployment name (`collector-webapp`) and cluster configuration.

6. **Error Notifications**:
   - Integrate a notification step to alert you (via Slack, email, or another service) if any step in the workflow fails:
     ```yaml
     - name: Notify on failure
       if: failure()
       uses: actions/notify-action@v1
       with:
         message: "Deployment failed. Check logs for details."
     ```
 