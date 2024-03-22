// pass through import paths to expose outside package
// index.js is "main" in package.json
module.exports = {
...require("./server-aac"),
...require("./aacWorker")
}