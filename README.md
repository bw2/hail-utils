To install, run 

```
python3 -m pip install git+https://github.com/bw2/hail-utils.git
```

To install in a dataproc cluster, run

```
print(subprocess.check_output(
    "/opt/conda/default/bin/python3 -m pip install git+https://github.com/bw2/hail-utils.git", 
    shell=True, encoding="UTF-8"))

```
