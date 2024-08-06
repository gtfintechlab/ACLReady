import React, { useEffect } from 'react';
import Sidebar from '../Sidebar/Sidebar';
import Question from '../Question/Question';
import { useStore } from '../../store';
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';
import ArrowBackIosNewIcon from '@mui/icons-material/ArrowBackIosNew';
import DownloadIcon from '@mui/icons-material/Download';
import { saveAs } from 'file-saver';

function Home() {
  const { state, dispatch } = useStore();
  const { responses, aclQuestions, currentStage, sectionProgress, timeTaken } = state;
  const listHeader = ['A', 'B', 'C', 'D', 'E'];

  useEffect(() => {
    aclQuestions.forEach(({id, quest}) => {
      Object.keys(quest.questions).sort((a, b) => {
        const numA = parseInt(a.slice(1), 10);
        const numB = parseInt(b.slice(1), 10);
        return numA - numB;
      })
      .forEach(questionId => {
        const response = responses[questionId];
        console.log(response)
      //   console.log(response.s_name)
      })
    })
  }, [])

  const generateMarkdown = () => {
    let markdown = "# ACL Responsible Checklist Responses\n\n";
    if(timeTaken) {
      markdown += `${timeTaken}\n\n`
    }

    aclQuestions.forEach(({ id, quest }) => {
      markdown += `## Section ${id}: ${quest.title}\n\n`;

      Object.keys(quest.questions).sort((a, b) => {
        const numA = parseInt(a.slice(1), 10);
        const numB = parseInt(b.slice(1), 10);
        return numA - numB;
      }).forEach(questionId => {
        const questionText = quest.questions[questionId];
        const response = responses[questionId];

        if (response) {
          markdown += `### ${questionId}: ${questionText}\n`;
          markdown += `**Yes/No:** ${response.choice == true ? 'Yes' : 'No'}\n\n`
          markdown += `**Response:** ${response.text}\n\n`;
        } else {
          markdown += `### ${questionId}: ${questionText}\n`;
          markdown += `**Response:** No response provided.\n\n`;
        }
      });
    });

    return markdown;
  };

  const handleDownload = () => {
    const markdownContent = generateMarkdown();
    const blob = new Blob([markdownContent], { type: 'text/markdown;charset=utf-8' });
    saveAs(blob, 'acl_responses.md');
  };

  return (
    <>
      <Sidebar />
      <div className='absolute height-fultop-0 bottom-72 w-full' />
      <div className="p-4 sm:ml-72 mt-10">
        <div className='rounded mr-5'>
          {aclQuestions && aclQuestions.map(({ id, quest }) => {
            if (id == currentStage) {
              return (
                <div key={id}>
                  <h1 className='text-3xl mb-6 text-center font-thin'><b>SECTION {id}</b></h1>
                  <div className='w-full flex align-center justify-center'>
                  <div className='flex ease-in duration-300 justify-center items-center bg-gray-500 w-fit rounded-full'>
        {listHeader.map(stage => (
          <div
          key={stage}
          className={`flex items-center text-xl py-1 font-semibold px-3 ${currentStage === stage ? 'bg-gray-700 text-white opacity-100' : 'bg-gray-500 text-white opacity-50'} rounded-full cursor-pointer`}
          onClick={() => dispatch({ type: 'SET_CURRENT_STAGE', payload: stage })}
          style={{ transition: 'all 0.3s ease-in-out' }} // Add transition here
        >
            {stage}
            {/* <progress
              className='mx-4 rounded-lg'
              value={sectionProgress[stage] || 0}
              max="100"
            ></progress> */}
            <div className="relative h-1 bg-gray-400 rounded-full overflow-hidden mx-4 w-24">
              <div
                className="progress-bar h-1 bg-white z-10"
                style={{ width: `${sectionProgress[stage] || 0}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>
      </div>
      <div className='p-24 pb-10 pt-12'>
                  <h1 className='times text-2xl font-bold'>{id} | <span className='font-normal'>{quest.title}</span></h1>
                  {quest.titleResponse == 1 && (
                    <Question key={id} id={id} question_data={null} isRoot={true} />
                  )}
                  {responses[id] != null && responses[id].choice == true && Object.entries(quest.questions)
                    .sort((a, b) => {
                      const numA = parseInt(a[0].slice(1), 10);
                      const numB = parseInt(b[0].slice(1), 10);
                      return numA - numB;
                    })
                    .map(([id2, question_data]) => (
                      <div key={id2}>
                        <Question id={id2} question_data={question_data} isRoot={false} className="mt-10" />
                        <hr className='my-6 mb-14' />
                      </div>
                    ))}

                    {quest.titleResponse == 0 && Object.entries(quest.questions)
                    .sort((a, b) => {
                      const numA = parseInt(a[0].slice(1), 10);
                      const numB = parseInt(b[0].slice(1), 10);
                      return numA - numB;
                    })
                    .map(([id2, question_data]) => (
                      <div key={id2}>
                        <Question id={id2} question_data={question_data} isRoot={false} className="mt-10" />
                        <hr className='my-6 mb-14' />
                      </div>
                    ))}

                    </div>
                </div>
              );
            }
            return null;
          })}
        </div>
        <div className='flex flex-row justify-between px-10 align-center mb-10'>
            <button onClick={() => {
              const listHeader = ['A', 'B', 'C', 'D', 'E'];
          let nextIndex = (listHeader.indexOf(currentStage) - 1);
          if(nextIndex < 0) nextIndex = 0;
          dispatch({ type: 'SET_CURRENT_STAGE', payload: listHeader[nextIndex] })
            }} className={`flex flex-row items-center justify-center text-lg ${currentStage == 'A' && 'opacity-20'}`}><ArrowBackIosNewIcon />&nbsp;&nbsp;Previous Section</button>
            
            <button className={`relative right-0 ${currentStage == 'E' && 'hidden'} text-lg`} onClick={() => {
              const listHeader = ['A', 'B', 'C', 'D', 'E'];
              let nextIndex = (listHeader.indexOf(currentStage) + 1);
              dispatch({ type: 'SET_CURRENT_STAGE', payload: listHeader[nextIndex] })
            }}>Next Section&nbsp;&nbsp;<ArrowForwardIosIcon /></button>
            {
          currentStage == 'E' && (
            <button onClick={handleDownload} className='bg-black text-white p-3 rounded-full'>Download Document&nbsp;&nbsp;<DownloadIcon /></button>
          )
        }
          </div>
      </div>
    </>
  );
}

export default Home;
