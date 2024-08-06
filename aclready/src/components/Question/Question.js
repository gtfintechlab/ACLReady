import React, { useState, useEffect } from 'react';
import { useStore } from '../../store';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import Tooltip from '@mui/material/Tooltip';

function Question({ id, question_data, isRoot }) {
  const { state, dispatch } = useStore();
  const { responses, issues } = state;
  const initialResponse = responses[id] || { choice: false, text: '' };
  let tempResponse = initialResponse.s_name + ". " +initialResponse.text;
  const [response, setResponse] = useState(tempResponse);
  const [choice, setChoice] = useState(initialResponse.choice);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(response).then(() => {
      // alert('Copied to clipboard');
    }).catch(err => {
      console.error('Failed to copy text: ', err);
    });
  };

  useEffect(() => {
    setResponse(initialResponse.text);
    setChoice(initialResponse.choice);
  }, [initialResponse.text, initialResponse.choice]);

  const handleResponseChange = (e) => {
    const newResponse = e.target.value;
    setResponse(newResponse);
    dispatch({ type: 'SET_RESPONSE', payload: { id, response: { choice, text: newResponse }}});
  };

  const handleChoiceChange = (newChoice) => {
    setChoice(newChoice);
    dispatch({ type: 'SET_RESPONSE', payload: { id, response: { choice: newChoice, text: response } } });
  };

  return (
    <div className='w-full flex flex-col mb-2' id={id}>
      {!isRoot && (
        <div className='flex flex-row justify-between items-center'>
        <h1 className='text-xl my-4'><b>{id}</b>&nbsp;&nbsp;|&nbsp;&nbsp;{question_data}</h1>
        <div className='bg-gray-500 flex flex-row w-fit rounded-full mb-5 h-fit ml-4'>
        <h1 className={`px-4 py-2 cursor-pointer text-white ease-in duration-300 rounded-full ${choice ? "bg-gray-700" : "bg-gray-500"}`}
            onClick={() => handleChoiceChange(true)}>YES</h1>
        <h1 className={`px-4 py-2 cursor-pointer text-white ease-in duration-300 rounded-full ${!choice ? "bg-gray-700" : "bg-gray-500"}`}
            onClick={() => handleChoiceChange(false)}>NO</h1>
      </div>
        </div>
      )}
      {
        isRoot ? (
          <div className='flex flex-row justify-between mb-10'>
            <p className='text-lg mb-4 mt-4'>If you answer <b>Yes</b>, answer the questions below; if you answer <b>No</b>, you can skip the rest of this section.</p>
            <div className='bg-gray-500 flex flex-row w-fit rounded-full mb-5 h-fit ml-4'>
            <h1 className={`px-4 py-2 cursor-pointer text-white ease-in duration-300 rounded-full ${choice ? "bg-gray-700" : "bg-gray-500"}`}
            onClick={() => handleChoiceChange(true)}>YES</h1>
        <h1 className={`px-4 py-2 cursor-pointer text-white ease-in duration-300 rounded-full ${!choice ? "bg-gray-700" : "bg-gray-500"}`}
            onClick={() => handleChoiceChange(false)}>NO</h1>
      </div>
      </div>
        ) : (
            <p className='text-lg mb-4'>If you answer <b>Yes</b>, provide the section number; if you answer <b>No</b>, provide a justification.</p>
        )
      }
      {/* {issues[id] != undefined && issues[id][0] == 1 && (
        <p className='py-2 text-red-500'>{issues[id][1]}</p>
      )} */}
      {!isRoot && (
        <div className='relative'>
          {/* ${issues[id] != undefined && issues[id][0] == 1 && "bg-red-100"} */}
          {/* ${issues[id] && issues[id][0] == 1 && "border-red-300"} */}
        <textarea
          className={`text-black bg-gray-100 h-24 border-2 rounded p-4 outline-none w-full`}
          placeholder={`${choice ? 'Mention section number and elucidate on it...' : 'Mention Justification ...'}`}
          value={response}
          onChange={handleResponseChange}
        />
        <Tooltip title="Copy to clipboard" aria-label="copy">
          <ContentCopyIcon
            onClick={copyToClipboard}
            className={`absolute bottom-2 right-2 m-2 cursor-pointer text-gray-500 hover:text-gray-700`}
          />
        </Tooltip>
      </div>
      )}
    </div>
  );
}

export default Question;
