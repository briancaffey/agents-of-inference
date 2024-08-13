# Kubernetes

This section is WIP

These resources are for setting up the inference environment on a local kubernetes cluster.

## Setup

- start a microk8s kubernetes cluster with the following add-ons:
    - nvidia
    - dashboard
    - registry
- check the plugins with `microk8s status`
- replace `HUGGING_FACE_HUB_TOKEN` value in `k8s/llm/hf-secret.yml`
- bring up the kuberenetes dashboard with `microk8s dashboard-proxy`

## Deploy resources

```
microk8s kubectl apply -f k8s/comfyui/storage.yml
microk8s kubectl apply -f k8s/comfyui/deployment.yml
microk8s kubectl apply -f k8s/comfyui/service.yml

microk8s kubectl apply -f k8s/llm/storage.yml
microk8s kubectl apply -f k8s/llm/hf-secret.yml
microk8s kubectl apply -f k8s/llm/deployment.yml
microk8s kubectl apply -f k8s/llm/service.yml
```

## TODO

The kubernetes environment is WIP. LLM inference with vLLM and ComfyUI are currently working.

- Better scheduling of ComfyUI and LLM workloads
- Add additional services for voice and music generation
- Add resources for main application (agents-of-inference)
- Use kustomize/Helm for easier deployment and configuration of resources