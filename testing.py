import os
import re
import subprocess
import tempfile

import re


def apply_patch(original_text: str, diff_text: str) -> str:
    """ Apply a diff using the patch command via temporary files """
    print('1')
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as original_file:
        original_file_name: str = original_file.name
        if original_text:
            original_file.write(
                original_text if original_text.endswith('\n') else original_text + '\n'
            )
    print('2')
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as diff_file:
        diff_file_name: str = diff_file.name
        diff_file.write(diff_text if diff_text.endswith('\n') else diff_text + '\n')
    print('3')
    try:
        # New file
        print('new file')
        if original_text == "" and "+++ " in diff_text:
            lines: list[str] = diff_text.split(sep='\n')
            new_content_lines: list[str] = [
                line[1:] if line.startswith('+') else line for line in lines[3:]
            ]
            new_content: str = '\n'.join(new_content_lines)
            with open(file=original_file_name, mode='w', encoding='utf-8') as new_file:
                new_file.write(new_content)

        # Modified or deleted file
        else:
            print('modified')
            with open(file=diff_file_name, mode='r', encoding='utf-8') as input_diff:
                subprocess.run(
                    args=['patch', '-u', original_file_name],
                    input=input_diff.read(),
                    text=True,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

        print("Patch applied successfully.")
        with open(file=original_file_name, mode='r', encoding='utf-8') as modified_file:
            modified_text: str = modified_file.read()
            print(f"{modified_text=}\n")

    except Exception as e:
        print("Failed to apply patch.")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}\n")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"Exit status: {e.returncode}")
        raise

    finally:
        os.remove(path=original_file_name)
        os.remove(path=diff_file_name)
        print("Temporary files removed.\n")

    return modified_text


def clean_specific_lines(text: str) -> str:
    lines: list[str] = text.strip().split(sep='\n')
    cleaned_lines: list[str] = [
        line for line in lines if not (
            line.startswith('```diff') or line == '```' or line.strip() == '')
    ]
    return '\n'.join(cleaned_lines).strip()


def extract_file_name(diff_text: str) -> str:
    match = re.search(pattern=r'^\+\+\+ (.+)$', string=diff_text, flags=re.MULTILINE)
    if match:
        return match.group(1)
    raise ValueError("No file name found in the diff text.")


def split_diffs(diff_text: str) -> list[str]:
    file_diffs: list[str] = re.split(pattern=r'(?=^---\s)', string=diff_text, flags=re.MULTILINE)

    # Remove the first element if it's an empty string
    if file_diffs and file_diffs[0] == "":
        file_diffs.pop(0)

    # Remove leading and trailing whitespace from each diff
    file_diffs = [diff.strip() for diff in file_diffs]
    return file_diffs
  
  
original_text = """import type { NextApiRequest, NextApiResponse } from "next";

import { z, ZodError } from "zod";

const schema = z.object({
  folderName: z.string(),
});

import { v2 as cloudinary } from "cloudinary";

cloudinary.config({
  cloud_name: "duaiiecow",
  api_key: "896513553396748",
  api_secret: "dtVnFQqHwz1WsYSUN3w52n6rqWs",
});

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "GET") {
    res.status(405).json({ message: "Method not allowed" });
    return;
  }

  try {
    const folderName = schema.parse(req.query).folderName;

    const images = await cloudinary.api.resources({
      type: "upload",
      prefix: folderName,
      max_results: 100,
    });
    const videos = await cloudinary.api.resources({
      type: "upload",
      resource_type: "video",
      prefix: folderName,
      max_results: 100,
    });

    let imageAssets = images.resources.map((resource: any) => ({
      public_id: resource.public_id,
      url: resource.secure_url,
    }));

    let videoAssets = videos.resources.map((resource: any) => ({
      public_id: resource.public_id,
      url: resource.secure_url,
    }));

    res
      .status(200)
      .json({ imageAssets: imageAssets, videoAssets: videoAssets });
  } catch (err) {
    console.error(err);
    if (err instanceof ZodError) {
      res.status(400).json({ message: err.issues[0].message });
    } else {
      res.status(500).json({ message: "Internal server error" });
    }
  }
  return;
}"""

diff="""@@ -0,0 +1,22 @@
+import type { NextApiRequest, NextApiResponse } from 'next';
+import { v2 as cloudinary } from 'cloudinary';
+
+export default async function handler(
+  req: NextApiRequest,
+  res: NextApiResponse
+) {
+  cloudinary.config({
+    cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
+    api_key: process.env.CLOUDINARY_API_KEY,
+    api_secret: process.env.CLOUDINARY_API_SECRET,
+  });
+
+  const { resources } = await cloudinary.search
+    .expression('folder:merch')
+    .sort_by('public_id', 'desc')
+    .max_results(30)
+    .execute();
+
+  const images = resources.map(({ public_id, secure_url }) => ({ public_id, url: secure_url }));
+  res.status(200).json({ images });
+}
"""
  

