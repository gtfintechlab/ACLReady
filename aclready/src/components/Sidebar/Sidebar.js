import React, { useState, useRef, useEffect } from 'react';
import aclLogo from '../../assets/aclready.png';
import AuthModal from '../AuthModal/AuthModal';
import { useStore } from '../../store';
import db, { auth } from '../../firebase';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import { useDropzone } from 'react-dropzone';

export default function Sidebar() {
  const [open, setOpen] = useState(false);
  const { state, dispatch } = useStore();
  const hiddenFileInput = useRef(null);
  const [loadingFile, setLoadingFile] = useState(false);
  const [jsonContent, setJsonContent] = useState(null);
  const [loadingStage, setLoadingStage] = useState("");
  const { getRootProps, getInputProps } = useDropzone({
    onDrop: (acceptedFiles) => {
      handleFileChangeDrop(acceptedFiles);
    },
  });

  const handleClick = () => {
    hiddenFileInput.current.click();
  };

  const handleFileUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      dispatch({
        type: 'SET_ISSUES',
        payload: {}
      })
      dispatch({
        type: 'SET_CURRENT_STAGE',
        payload: 'A'
      })
      dispatch({
        type: 'SET_TIME',
        payload: ''
      })
      dispatch({
        type: 'RESET_RESPONSE'
      })
      dispatch({
        type: 'RESET_PROGRESS'
      })
      setLoadingStage("Loading...");

      const eventSource = new EventSource('http://localhost:8080/api/upload/status');

      eventSource.onmessage = function(event) {
        setLoadingStage(event.data);
      };

      const response = await fetch('http://localhost:8080/api/upload', {
        method: 'POST',
        body: formData,
      });

      eventSource.close();

      const result = await response.json();
    if (result.error) {
      alert(result.error);
    } else {
      setJsonContent(result);
      console.log(result)
      dispatch({
        type: 'SET_TIME',
        payload: result['time_taken']
      })
      dispatch({
        type: 'SET_ISSUES',
        payload: result['issues']
      })
      for (const key in result) {
        let section_name = result[key]['section name'];
        dispatch({
          type: 'SET_RESPONSE',
          payload: {
            id: key,
            response: {
              choice: section_name == 'None' ? false : true,
              text: section_name + ". " +result[key]['justification'],
              s_name: section_name,
            },
          },
        });
      }
    }
  } catch (error) {
    console.error('Error uploading file:', error);
  } finally {
    setLoadingFile(false);
  }
};

  const handleChange = async (event) => {
    const fileUploaded = event.target.files[0];
    let file_size = fileUploaded.size;

    setLoadingFile(true);

    if (file_size > 5000000) {
      alert("File size should not exceed 5MB.");
      setLoadingFile(false);
      return;
    }

    await handleFileUpload(fileUploaded);
  };

const handleFileChangeDrop = async (filesAccepted) => {
    const fileUploaded = filesAccepted[0];
    let file_size = fileUploaded.size;

    setLoadingFile(true);

    if (file_size > 5000000) {
      alert("File size should not exceed 5MB.");
      setLoadingFile(false);
      return;
    }

    await handleFileUpload(fileUploaded);
  };

  useEffect(() => {
    // This useEffect can be used to set any initial state if needed
  }, []);

  const handleClickOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  
  return (
    <>
     <div className={`fixed w-full h-full bg-[rgba(0,0,0,0.7)] z-50 top-0 left-0 flex items-center justify-center ${loadingFile ? '' : 'hidden'} flex flex-col`}>
  <img id="loading-logo" className="h-40 rounded-full animate-pulse" src={aclLogo} alt="Logo" />
  <h1 className='text-white text-2xl m-6 animate-pulse'>{loadingStage}</h1>
</div>


      <AuthModal open={open} onClose={handleClose} />

      <aside
        id="logo-sidebar"
        style={{borderTopRightRadius: 120}}
        className="fixed top-0 left-0 z-40 w-72 h-screen pt-10 transition-transform -translate-x-full border-r sm:translate-x-0 bg-gray-800 border-gray-700 items-center flex flex-col justify-between"
        aria-label="Sidebar"
      >
        <div className="flex flex-col mt-12 justify-center items-center">
          <div className="px-3 pb-4 overflow-y-auto bg-white dark:bg-gray-800">
            <img src={aclLogo} className="h-[150px]" />
          </div>
          <p className="text-white text-center px-8 lekton">
            AI powered solution for seamlessly filling out the ACL Responsible Checklist.
          </p>
        </div>
        <aside
        style={{borderTopRightRadius: 120}}
        className="z-40 w-72 h-screen mt-10 transition-transform -translate-x-full border-r sm:translate-x-0 bg-[#003057] border-[#003057] items-center flex flex-col"
      >
        <h1 className='text-white font-bold text-base mt-12'>Upload Document</h1>
        
        <div {...getRootProps()} onClick={() =>handleClick()} className='cursor-pointer border-dotted m-6 py-28 rounded-sm border-2 border-white w-64 flex flex-col items-center'>
        <input
        {...getInputProps()}
        type="file"
        accept=".tex"
        onChange={handleChange}
        ref={hiddenFileInput}
        style={{display: 'none'}}
      />
        {loadingFile ? (
                  <div className="container flex justify-center mb-7"><div className="loader">
  <div></div>
  <div></div>
  <div></div>
</div></div>
                ):(
                  <AddCircleIcon className='text-white' fontSize="large" />
                )}
          <p className='text-white text-center lekton m-2 mt-6'>{!loadingFile ? 'Upload or drag and drop your file here' : 'Please Wait...'}</p>
        </div>
      </aside>
      </aside>
    </>
  );
}
