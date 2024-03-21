/**
 * Express server.
 * 
 * https://create-react-app.dev/docs/getting-started
 */
"use strict";
const args = process.argv;

const app = (options) => {
  if(options === undefined) options = {};
  if(options.port === undefined) options.port = 8081;

  const args = process.argv;
  const cors = require('cors');
  const path = require("path");
  const express = require('express');
  const fileupload = require("express-fileupload");
  const { open } = require('out-url');
  const app = express();
  const aacWorker = require("./aacWorker");
  const PORT = process.env.PORT || options.port;
  

  
  app.use(
      fileupload({
        createParentPath: true,  // may create upload folder
      })
    );
  app.use(cors())
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));
  app.use(express.static(path.join(__dirname, 'build')));  // react build folder, browser index.html page
  
  // Opens the URL in the default browser.
  if(options.browser) open('http://localhost:' + PORT);
  
  app.post("/api/upload-file", cors(), (req, res, next) => {   // cors enabled for this route
  try {
      if (!req.files) {
        res.send({
          status: "failed",
          message: "No file uploaded",
        }); 
      } else {
        let outputFolder = req.body["outputFolder"];
        let fArr = req.files["fileArray"];
  
        let fArrLength = fArr.length;
        if(fArrLength === undefined || fArrLength === null) {  // just one file inside, {outputFolder: {}} is dict
          aacRepair({
            fileArray: fArr,
            outputFolder: outputFolder,
            response: res,
            singleFile: true,
          });
          return;  // else res header error
        } else {  // multi files {outputFolder: [ {}, {}, {}] } is array
          aacRepair({
            fileArray: fArr,
            outputFolder: outputFolder,
            response: res,
            singleFile: false,
          });
          return;
        }
      }
    } catch (err) {
      res.status(500).send(err);
    }
    next();  // if next app.get("/upload-file", is the same route as here, we can proceed to those fun and send "res.end();"
  })
  
  function aacRepair(opt) {
    (async () => {
      let singleFile = undefined;
      let multiFile = undefined;
      let msgSuccess = "Bytes cut - File";
  
      if(opt.singleFile) {
        singleFile = new Promise((resolve, reject) => {
            resolve(aacWorker.writeOneRepaired(
                      opt.fileArray.data, 
                      path.join(opt.outputFolder, 
                      opt.fileArray.name), opt.outputFolder
                      ));
            reject(err);
        })
        singleFile.then((cutBytes) => {
          opt.response.send({ 
            status: "ok", 
            message: msgSuccess,
            data: [{name: opt.fileArray.name, size: cutBytes}]
          });
        });
        return;
      }
  
      multiFile = async () => {
        let fileCutArr = [];
        let size = 0;  // extract from resolve context
        let name = "";
        for (const file of opt.fileArray) {
  
          await aacWorker.writeOneRepaired(
                  file.data, path.join(opt.outputFolder, 
                  file.name), 
                  opt.outputFolder
                  )
            .then(cutBytes => {
              size = cutBytes;
              name = file.name;
            })
            .catch(error => {
              size = 0;
              name = error.message;
            });
          
          fileCutArr.push({name: name, size: size});
        }
        return fileCutArr;
      }
      multiFile()
        .then((nameCutSizeList) => {
          opt.response.send({ 
            status: "ok", 
            message: msgSuccess, 
            data: nameCutSizeList});
        })
      
    })();
    return;
  }
  
  app.get('/foo', (req, res) => {  
      res.setHeader('Content-Type', 'text/plain');
      res.send('foo is not bar!')
  })
  
  
  app.listen(PORT, () => {
        console.log('server listening on port ' + PORT)
  })
}
if(args[2] === "--frontend") app( {browser: true} );

module.exports = { app }