// https://www.codeproject.com/Questions/5345782/How-to-submit-multiple-files-with-multiple-text-fi
// https://www.bezkoder.com/react-typescript-file-upload/
// https://www.typescriptlang.org/docs/handbook/utility-types.html
import { useForm } from "react-hook-form";
import React, { useState } from 'react';
import './App.css';

const formDataKeyFile = "fileArray";
const formDataKeyStorage = "outputFolder";
const fileUploadUrl = "http://localhost:8081/api/upload-file"


const App: React.FC = () => {

  const [currentFile, setCurrentFile] = useState<FileList>(); 
  const [outputFolder, setOutputFolder] = useState<string>(""); 
  const [msgResult, setMsgResult] = useState<string>();
  const [dataResult, setDataResult] = useState<string[]>([]); 
  const { register, handleSubmit } = useForm();
  
  interface GetResponse {
    message: string,
    data: Array<{
      size: number,
      name: string
    }>,
  }
  const onSubmit = async (data: any): Promise<void> => {
    const formData = new FormData();  // {fileArray → {}, fileArray → {}, fileArray → {}, outputFolder → "/home/joe/Dl"}
    for (const key of Object.keys(data.file) as Array<keyof typeof File>) {  // "req.files"
      formData.append(formDataKeyFile, data.file[key]);  
    }
    formData.append(formDataKeyStorage, outputFolder);  // "req.body"

    const res: GetResponse = await fetch(fileUploadUrl, {
      method: "POST",
      body: formData
    })
    .then((res) => res.json())  // stringify uses
    const msg: string = res.message;
    const dataArray: string[] = [...res.data].map((data) => data.size + " - " + data.name);
    setMsgResult(msg);
    setDataResult(dataArray);
  };

  const handleChangeInputTextFolder = (event: React.ChangeEvent<HTMLInputElement>) => setOutputFolder(event.target.value);

  const handleSelectedFile = (event: React.ChangeEvent<HTMLInputElement>): void => {
    setCurrentFile(event.target.files as FileList);
    setMsgResult("");
    setDataResult([]);
  }
  const SelectedFiles = () => {  // also: function SelectedFiles() {}
    let fileNameArray: string[] = [" "];
    if(currentFile !== undefined) fileNameArray = [...currentFile].map((file) => file.name);
 
    return (
      <div className="SelectedFiles">
        <div>file count: {currentFile?.length}</div>
        {fileNameArray.map((name) => <div key={name}>{name}</div>)}
      </div>
    )
  }
  const RepairResult = () => {
    return (
      <div className="RepairResult">
        {<div> { msgResult }</div>}
        {dataResult.map(row => <div key={row}>{row}</div>)}
      </div>  
    )
  }
  return (
    <div className="App">
      <span className="heading">AAC repair</span>
      <p className="pFolder">Repair internet stream-, or personal recordings.</p>
      <p className="pFolder">.aac/.aacp - clean cut file header and payload  </p>
      <form onSubmit={handleSubmit(onSubmit)} encType="multipart/form-data">

        <input type="text" 
              placeholder="/home/foo/outputAacRepair"
              className="input__box"
              id="inputTextFolder"
              onChange={handleChangeInputTextFolder}         
              required/>
              <br/>
        <label htmlFor="inputFileUpload"> 
          <input type="file" {...register('file', { required: true })}
              accept=".aac, .aacp"
              id="inputFileUpload"
              // hidden // NO NO, stops working, use opacity 
              multiple
              onChange={handleSelectedFile}
              />
              
            <div className="input__submit"
                  id="input__submit__files">
              files
              </div>  
        </label>       
        <button type="submit" 
               className="input__submit"
               id="input__submit__send">
                Go
               </button>
               <RepairResult/>
               <SelectedFiles/>
      </form>
    </div>
  );
}

export default App;
