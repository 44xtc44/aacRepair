// aacWorker.js
"use strict";

/**
* Python AAC sound file repair to node js translation.
* Added an express web server to the package.
* "Creating a React, Node, and Express App"
* Can repair a folder like so "node aacWorker './damagedFiles'"
* @author René Horn
* @author www.github.com/44xtc44
* @version 1.0
* @since 1.0
* @see license MIT  
 */

const cl = console.log;
const args = process.argv;
const fs = require("fs-extra");
const path = require("path")
var fileArray = [];  // cmd line use
const os = require('os');

/**
 * "byteToHex"; pre-computes the 2-character hex octets for every possible value of an unsigned byte: [0, 255], 
 * "doHex(arrayBuffer)" maps each value in the ArrayBuffer through the array of octet strings. 
 */
const byteToHex = [];
for (let n = 0; n <= 0xff; ++n) {
    const hexOctet = n.toString(16).padStart(2, "0");
    byteToHex.push(hexOctet);
}
function doHex(arrayBuffer) {
    const buff = new Uint8Array(arrayBuffer);
    const hexOctets = []; // new Array(buff.length) is even faster (preallocates necessary array size), then use hexOctets[i] instead of .push()

    for (let i = 0; i < buff.length; ++i)
        hexOctets.push(byteToHex[buff[i]]);
    return hexOctets.join("");
}

/**
 * AAC or AACP file has header fff9 or fff1 hex followed by the payload.
 * @param {*} chunk 
 * @returns array
 */
function repairHead(chunk)
{
  let start = 0;
  let end = 2;

  if (chunk.byteLength < end) {
      // self.error_dict[fName] = "File is smaller than aac header search frame - ignore it."
      cl("File is smaller than aac header search frame - ignore it.", chunk.byteLength)
      return;
  }
  
  while (true){
    if (end > chunk.byteLength) {
      // self.error_dict[fName] = "File has no aac header - ignore it."
      return false;
    }
    if(/fff9|fff1/.test(doHex(chunk.slice(start, end)))) {
      return chunk.slice(start);
    }
    start += 1
    end += 1
  }
}
function repairTail(chunk)
{
  let start = -1;
  let end = -3;
  
  while (true){
    if (end < -(chunk.byteLength)) {
      return false;
    }
    if(/fff9|fff1/.test(doHex(chunk.slice(end, start)))) {
      return chunk.slice(0, end);
    }
    start -= 1
    end -= 1
  }
}

function fileArrayGet(folderPath) {
  // return array of file paths ['damaged\\tyga - Taste feat Offset.aac','damaged\\Mir - mir san mir.aac']
  let fileArray = [];
  const isFile = fileName => {  // remove subfolder names
    return fs.lstatSync(fileName).isFile();
  };
  const isAacExtension = fileName => {
    let ext = path.extname(fileName);
    if(ext === ".aac" || ext === ".aacp") {
      return true;
    }else {
      return false;
    }
  };
  try {
    fileArray = fs.readdirSync(folderPath)
    .map(fileName => {
    return path.join(folderPath, fileName);
    })
    .filter(isFile)
    .filter(isAacExtension);
  } catch (err) {
    cl("Error reading folder in fileArrayGet()", err)
  }
  return fileArray;
}

function readOneFile(filePath) {
  // return input for oneFileRepair()
  return new Promise((resolve, reject) => {
    fs.readFile(filePath, function (err, nodeBuffer) {
      if (err) {
        reject(err);  // negative "return" of promise
      }
      resolve(nodeBuffer);  // positive "return" of promise
    });
  });
}

async function writeOneFile(opt) {
  return new Promise((resolve, reject) => {
    fs.writeFile(opt.fileName, opt.data, (err) => {
      if(err) {
        console.log(opt.fileName, err);
        reject(err);
      }else {
        console.log(opt.fileName, "Written to File.");
        resolve("ok write");
      }
    });
  });
}

async function processFilesCmd() {
  let msg = "All items processed";
  let dumpPath = "aacRepaired";
  for (const fileName of fileArray) {
    let fileDir = path.dirname(fileName);
    let newFileDir = path.join(fileDir, dumpPath);
    let fileBase = path.basename(fileName);
    let fileNew = path.join(fileDir, dumpPath , fileBase);
    let fileContent = await readOneFile(fileName);
    let headCut = await repairHead(fileContent);
    let tailCut = await repairTail(headCut);
    let cutByte = fileContent.byteLength - tailCut.byteLength;
    let fName = path.basename(fileNew);
    console.log(" [" + cutByte + "] bytes cut, " + fName);
    await makeFolder(newFileDir);
    writeOneFile({
      data: tailCut,
      fileName: fileNew, 
    })
    .catch((err) => {console.log(err);});
  }
  cl(msg);
}

function repairAacFolder(folderName) {
  if(folderName) {
    fileArray = fileArrayGet(folderName);
  } else if(args[2] === "-d") {
    fileArray = fileArrayGet(args[3]);  // node aacWorker.js "./damaged"
  } else {
    return;
  }
  console.log(fileArray)
  processFilesCmd();
}
repairAacFolder();  // if run node js from terminal

async function repairOneFileAac(fileContent) {
  // non aac/aacp file extension are already prefiltered by HTML selector
  let headCut = await repairHead(fileContent);
  let tailCut = await repairTail(headCut);
  return tailCut;
}

async function makeFolder (directory) {
  const desiredMode = 0o2775
  const options = {
  mode: 0o2775
}
  try {
    await fs.ensureDir(directory, options)
    console.log('makeFolder success! ' + directory)
  } catch (err) {
    console.error('Fail makeFolder! -> ' + err)
  }
}

async function writeOneRepaired(fileContent, fileNew, outputFolder) {

  return new Promise((resolve, reject) => {
    makeFolder(outputFolder)
    .then(() => repairOneFileAac(fileContent))  // check write fail later
    .then((byteData) => {
    writeOneFile({  
      data: byteData,
      fileName: fileNew, 
    })
    .then(() => {
      let cutByte = fileContent.byteLength - byteData.byteLength;
      resolve(cutByte)
      let fName = path.basename(fileNew);
      console.log(" [" + cutByte + "] bytes cut, " + fName);
    })
    .catch((error) => {
      console.log("writeOneFile->>>", error);
      reject(error)
    });

  })
  .catch((err) => {console.log("writeOneRepaired ->", err);});
  })
}

function cutOneByteAacFolder(folderName) {
  if(folderName) {
    fileArray = fileArrayGet(folderName);
  } else if(args[2] === "-d") {
    fileArray = fileArrayGet(args[3]);  // node aacWorker.js "./damaged"
  } else {
    return;
  }
  console.log(fileArray)
  cutOneByte();
}

async function cutOneByte() {
  let msg = "All items processed";
  let dumpPath = "aacDamaged";
  for (const fileName of fileArray) {
    let fileDir = path.dirname(fileName);
    let newFileDir = path.join(fileDir, dumpPath);
    let fileBase = path.basename(fileName);
    let fileNew = path.join(fileDir, dumpPath , fileBase);
    let fileContent = await readOneFile(fileName);
    let cutContent = fileContent.slice(1);  // cut one Byte at start
    let cutByte = fileContent.byteLength - cutContent.byteLength;
    let fName = path.basename(fileNew);
    console.log(" [" + cutByte + "] bytes cut, " + fName);
    await makeFolder(newFileDir);
    writeOneFile({
      data: cutContent,
      fileName: fileNew, 
    })
    .catch((err) => {console.log(err);});
  }
  cl(msg);
}

module.exports = {
  repairAacFolder,
  makeFolder,
  writeOneRepaired,
  readOneFile,
  repairOneFileAac,
  repairHead,
  repairTail,
  cutOneByteAacFolder
}