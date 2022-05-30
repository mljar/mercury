<h1> Output Files </h1>

You can easily create files in your notebook and allow your users to download them. 

Below are described steps how to add output files to the notebook.

### Step 1 - Define cell with YAML 

The YAML in the first RAW cell.

```yaml
title: My app
description: App with file download
params:
    output_dir:
        output: dir
```

The `output_dir` is the name of the variable that will be used in the code to store the path to output directory. All files saved in the output directory will be available to download for end-users.

### Step 2 - Variable with output directory

The next cell should have a variable with output directory path (in our example it is `output_dir`). Before the notebook execution an output directory will be created and its path will be assigned to this variable. 


```py
output_dir = "example_output_directory"
```

!!! note "All interactive variables in one code cell"

    Please remember to define all variables that are interactive in Mercury in one cell, just after the YAML header. That's the only requirement to make it work, but is very important.


### Step 3 - Use the output directory

In the next cells, just write files to the `output_dir`:

```py
import os
with open(os.path.join(output_dir, "my_file.txt"), "w") as fout:
    fout.write("This is a test")
```

### Step 4 - Output files in the web app

In the Mercury application, there will be additional menu in the sidebar with `Output files` button. Please click there to see your files. Each file in the directory can be downloaded.

<img 
    style="border: 1px solid #e1e4e5"
    alt="Output files in Mercury"
    src="../media/output-files-notebook.png" width="100%" />