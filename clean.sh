#!/bin/bash                                                                                                           

# List redundant .hs files for deletion
 
FOLDER="./n"

prev=""
for i in $FOLDER/*.hs ; do
    if [ -n "$prev" ]; then
        python compare_files.py "$prev" "$i"
        if [ $? -eq 0 ]; then
            echo "$i is not new, deleting"
            echo "$i" >> to_delete.txt
        else
            echo "$i is new"
        fi
    fi
    prev="$i"
done

echo "To delete: use cat to_delete.txt | xargs -I {} rm {}"
