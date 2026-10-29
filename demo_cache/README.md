# Demo images

The container copies the `*.npz` files in this folder into its image cache, so the example places open at once
instead of downloading Sentinel-2 scenes first. The files are not in git (they are about 18 MB).

To fill it:

```bash
.venv/Scripts/python -m scripts.prepare_demos
cp cache/composites/*.npz demo_cache/
```

Without them the container still works; each example then downloads its images the first time it is opened.
`scripts/deploy_space.py` uploads them to the Hugging Face Space along with the code.
