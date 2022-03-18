# Output Files

You can easily create files in your notebook and allow your users to download them. 

Below are described steps how to add output files to the notebook.

### Step 1 - define cell with YAML 

The YAML in the first RAW cell.

```yaml
title: My app
description: App with file download
params:
    output_dir:
        output: dir
```

### Step 2 - variable with output directory

The next cell should have a variable containing the directory name. The variable should be exactly the same as in YAML. This variable will have assigned a new directory name that will be created for your user during notebook execution. Please remember to define all variables that are interactive in Mercury in one cell, just after the YAML header (that's the only requirement to make it work, but is very important).

```py
output_dir = "example_output_directory"
```

### Step 3 - use the output directory

In the next cells, just produce files to the `output_dir`:

```py
import os
with open(os.path.join(output_dir, "my_file.txt"), "w") as fout:
    fout.write("This is a test")
```

### Step 4 - output files view in the web app

In the Mercury application, there will be additional menu in the top with `Output files` button. Please click there to see your files. Each file in the directory can be downloaded.

![Output files in Mercury](https://user-images.githubusercontent.com/6959032/153185874-f24cd6fe-9c64-4fa5-8b41-3814856d330a.png)

