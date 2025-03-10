# Requirements
* python 3.13 
* poetry
  * `pip install poetry`

# Installation
```bash
poetry install
```
# Usage
```bash
poetry run python src/scanner.py
```
## Output
```bash
Function Name                                                          Stack Name                               Parent Stack                            
SC-456389336637-pp-47i4nl-CleanupReplicasLambdaFun-KMsmRg24wfGK        SC-456389336637-pp-47i4nlaolwjh4         No parent stack found                   
SC-456389336637-pp-gnw7qc-GeneratePasswordLambdaFu-BazTWMrqTOBx        SC-456389336637-pp-gnw7qc7hgo7ew         integration-test-redis-cluster          
SC-456389336637-pp-gn4kh4rjwmoy4-ConvertToJson-0vLAhkeDey1u            SC-456389336637-pp-gn4kh4rjwmoy4         No parent stack found                   
SC-456389336637-pp-gnw7qc-ElasticacheRotationLambd-M2YkA1wDIOzH        SC-456389336637-pp-gnw7qc7hgo7ew         integration-test-redis-cluster
```