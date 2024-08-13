# Changelog

## [0.11.0](https://github.com/briancaffey/agents-of-inference/compare/v0.10.1...v0.11.0) (2024-08-13)


### Features

* **documentary:** add a new mode for generation ([14751cb](https://github.com/briancaffey/agents-of-inference/commit/14751cb74e6f756462152edc6d1185d4175f9345))

## [0.10.1](https://github.com/briancaffey/agents-of-inference/compare/v0.10.0...v0.10.1) (2024-08-08)


### Bug Fixes

* **k8s:** remove hostpath storage and replace with pv using node affinity and FileSystem volumeMode with local path ([299f7ac](https://github.com/briancaffey/agents-of-inference/commit/299f7ac1d62a519e78c1804c1768a2865035a00b))

## [0.10.0](https://github.com/briancaffey/agents-of-inference/compare/v0.9.0...v0.10.0) (2024-08-06)


### Features

* **k8s:** add kubernetes resources for vllm and comfyui ([74b3b22](https://github.com/briancaffey/agents-of-inference/commit/74b3b228f6356bd2418a9b01bf62a456b9bc7066))

## [0.9.0](https://github.com/briancaffey/agents-of-inference/compare/v0.8.0...v0.9.0) (2024-06-29)


### Features

* **chattts:** add chattts service for text to speech ([75803fc](https://github.com/briancaffey/agents-of-inference/commit/75803fc59b719106e43267fab98000683a88db84))
* **chattts:** wip add chattts service using gradio-client ([83428f6](https://github.com/briancaffey/agents-of-inference/commit/83428f6d8c2796f797359df2aa9e51271fade48a))

## [0.8.0](https://github.com/briancaffey/agents-of-inference/compare/v0.7.1...v0.8.0) (2024-06-27)


### Features

* **musicgen:** add musicgen service to be used for generating music ([3155ea5](https://github.com/briancaffey/agents-of-inference/commit/3155ea57815e32bf6c16220bdfad767bb55d6534))

## [0.7.1](https://github.com/briancaffey/agents-of-inference/compare/v0.7.0...v0.7.1) (2024-06-24)


### Bug Fixes

* **comfyui:** remove hardcoded url ([81281ea](https://github.com/briancaffey/agents-of-inference/commit/81281eadeb165786ce72a4ad0e227df1171c59dc))
* **readme:** update readme and docstrings with installation instructions ([caec523](https://github.com/briancaffey/agents-of-inference/commit/caec523c0d10bd036f15526d75bd71fc9f40446d))

## [0.7.0](https://github.com/briancaffey/agents-of-inference/compare/v0.6.0...v0.7.0) (2024-06-24)


### Features

* **trt:** replace svd engine with svdxt engine optimized for more frames ([ec21f9c](https://github.com/briancaffey/agents-of-inference/commit/ec21f9c03d5e1eb5dd7b822a0325d5cad965b2f1))


### Bug Fixes

* **generations:** add test generations ([016bef5](https://github.com/briancaffey/agents-of-inference/commit/016bef52a8a300f091e803232a30b784de18246a))

## [0.6.0](https://github.com/briancaffey/agents-of-inference/compare/v0.5.0...v0.6.0) (2024-06-24)


### Features

* **langsmith:** add langsmith api key to sample env and various bugfixes ([d88f207](https://github.com/briancaffey/agents-of-inference/commit/d88f207fd086705a5dc2ac814cc20fc25289415a))
* **tensorrt:** replace sd and svd services with comfyui-tensorrt accelerated workflow ([9a67eec](https://github.com/briancaffey/agents-of-inference/commit/9a67eecde229a2063360bdf0d204be6fb143a6ac))

## [0.5.0](https://github.com/briancaffey/agents-of-inference/compare/v0.4.0...v0.5.0) (2024-06-23)


### Features

* **trt-llm:** update prompts to work with both llama3 tensortrt-llm and q4_k_m gguf inference ([1b7899d](https://github.com/briancaffey/agents-of-inference/commit/1b7899d38ae40b35d84b5528e4c8a2d193e16583))

## [0.4.0](https://github.com/briancaffey/agents-of-inference/compare/v0.3.0...v0.4.0) (2024-06-17)


### Features

* **edges:** wip conditional edges in graph ([dc3683d](https://github.com/briancaffey/agents-of-inference/commit/dc3683d70372b892c0726b648831008f2663e7da))
* **readme:** update readme ([cb13ff3](https://github.com/briancaffey/agents-of-inference/commit/cb13ff3fb6e7c4d44a83f9e33d9565e9084ed484))
* **synopsis_review:** add synopsis review agent using conditional edges ([d3c1971](https://github.com/briancaffey/agents-of-inference/commit/d3c197141842eb6a96060148489dad0f45832d54))
* **viz:** add graph vizualization step ([cc00fd9](https://github.com/briancaffey/agents-of-inference/commit/cc00fd99463f58237724ee2c30636c35a8b7afd8))


### Bug Fixes

* **output:** cleanup old unused output ([4fb53d1](https://github.com/briancaffey/agents-of-inference/commit/4fb53d1f9771e23d20d8762218fbe47534a1ed1e))
* **svg:** langchain svg logo color ([fd08dc5](https://github.com/briancaffey/agents-of-inference/commit/fd08dc5c234b3cfb50fe5910ba79d0c4e122ebb3))

## [0.3.0](https://github.com/briancaffey/agents-of-inference/compare/v0.2.0...v0.3.0) (2024-06-11)


### Features

* **faceid:** wip faceid with comfyUI for consistent characters ([289b376](https://github.com/briancaffey/agents-of-inference/commit/289b3763d2aae8f35566ce51a4ab86a14095c7b1))
* **moviepy:** add generation of final movie with text strips showing SD prompts ([b95b51a](https://github.com/briancaffey/agents-of-inference/commit/b95b51a5f4dd73b84d4b93bd720e88b813e7746f))

## [0.2.0](https://github.com/briancaffey/agents-of-inference/compare/v0.1.0...v0.2.0) (2024-06-06)


### Features

* **langchain:** add langchain and langgraph with simple example ([9cf6d12](https://github.com/briancaffey/agents-of-inference/commit/9cf6d12b2a6a77119b01979801fbca66f82d7c8a))
* **moviepy:** add agent for creating movies with moviepy ([4eddd54](https://github.com/briancaffey/agents-of-inference/commit/4eddd54e4dcea686d574695c2880cec0bd6e1d0c))
* **mvp:** mvp for agents of inference ([0103fde](https://github.com/briancaffey/agents-of-inference/commit/0103fde3110d2d847c8a594db0637a08f7267180))
* **svd:** add a simple fastapi service for img2vid with svd ([0a0a9b8](https://github.com/briancaffey/agents-of-inference/commit/0a0a9b8bf38837113de0c907f86664babad734c9))
* **svd:** finished working version of stable video diffusion agent ([7fe992e](https://github.com/briancaffey/agents-of-inference/commit/7fe992ee1b9f0dd76d39f4ee9f579c6405416829))
* **svd:** fixes for svd service ([17a08aa](https://github.com/briancaffey/agents-of-inference/commit/17a08aa737bf4b6e5fe9235a4e6cc50e267642ad))
* **video:** add blender script for title scene ([e06018b](https://github.com/briancaffey/agents-of-inference/commit/e06018b3c9ab5e6caad35df45f15b76c7fe9935e))


### Bug Fixes

* **svd:** remove break from svd loop ([847607c](https://github.com/briancaffey/agents-of-inference/commit/847607c4fd1424ee4378597df9ee0cbb3e81d658))

## 0.1.0 (2024-06-02)


### Features

* **release-please:** add release please ([805bc9f](https://github.com/briancaffey/agents-of-inference/commit/805bc9f320298e344d2b6296ae7784a05fec7ba2))
