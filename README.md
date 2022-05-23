# Global Playlist

To run locally:

```
python generate_playlists.py
```


## TODO
Some missing features:
- Limits per language to reduce the number of songs we get in the more common languages
- Packaging to make lambda deployments easy
- Functionality to invalidate playlist cache
- Easier creds setup somehow?

## Packaging
1. Install dependencies:
```
$ pip install --target ./package requests --no-user
```
2. Zip the `./package` directory
3. Copy `lambda_function.py` and `global_playlist/` into the root of the archive
4. Upload to lambda
5. ???
6. Profit