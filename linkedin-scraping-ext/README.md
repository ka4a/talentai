## Note

`zookeep` chrome extension currently doesn't work as it used to bypass CSRF checks. See [ZOO-1231](https://stratakk.atlassian.net/browse/ZOO-1231) for details.

## Development

1. Run backend and dashboard dev server
2. `npm run start`
3. Open extensions page in a browser
4. Enable developer mode
5. Load unpacked extension from `build` folder

In development environment, it's using `localhost:3000` as backend

To see console log and requests, click "background page" on extensions page

## Publishing

1. `npm run build`
2. Pack `build` **folder content** to zip
3. Upload zip file to store
