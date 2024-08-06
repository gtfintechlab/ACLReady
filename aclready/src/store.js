import React, { createContext, useReducer, useContext, useEffect } from 'react';
import { collection, getDocs } from 'firebase/firestore';
import db, { auth } from './firebase';
import { onAuthStateChanged } from 'firebase/auth';

const StoreContext = createContext();

const initialState = {
  aclQuestions: [],
  currentStage: 'A',
  responses: {'B': {'choice': true }, 'C': {'choice': true }, 'D': {'choice': true }, 'E': {'choice': true }},
  sectionProgress: {},
  user: null,
  timeTaken: '',
  issues: {}
};

const calculateProgress = (responses, aclQuestions) => {
  const progress = {};

  // Initialize progress count for each section
  aclQuestions.forEach(section => {
    const sectionId = section.id;
    const numOfQuestions = section.quest.numOfQuestions;
    progress[sectionId] = { total: numOfQuestions, answered: 0 };
  });

  // Count the number of answered questions in each section
  for (const key in responses) {
    for (const section of aclQuestions) {
      const questionIds = Object.keys(section.quest.questions);
      if (questionIds.includes(key) && responses[key].text) {
        progress[section.id].answered += 1;
      }
    }
  }

  // Convert counts to percentage progress
  for (const section in progress) {
    progress[section] = (progress[section].answered / progress[section].total) * 100;
  }

  return progress;
};

const reducer = (state, action) => {
  switch (action.type) {
    case 'SET_QUESTIONS':
      return {
        ...state,
        aclQuestions: action.payload,
      };
    case 'SET_ISSUES':
       return {
        ...state,
        issues: action.payload,
      };
    case 'SET_CURRENT_STAGE':
      return {
        ...state,
        currentStage: action.payload,
      };
    case 'SET_TIME':
      return{
        ...state,
        timeTaken: action.payload
      };
    case 'SET_RESPONSE':
      const updatedResponses = {
        ...state.responses,
        [action.payload.id]: action.payload.response,
      };
      const updatedProgress = calculateProgress(updatedResponses, state.aclQuestions);
      return {
        ...state,
        responses: updatedResponses,
        sectionProgress: updatedProgress,
      };
    case 'RESET_RESPONSE':
      return {
        ...state,
        responses: {'B': {'choice': true }, 'C': {'choice': true }, 'D': {'choice': true }, 'E': {'choice': true }}
      }
    case 'RESET_PROGRESS':
      return {
        ...state,
        sectionProgress: {}
      }
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
      };
    default:
      return state;
  }
};

export const StoreProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const querySnapshot = await getDocs(collection(db, 'aclchecklist'));
        const questions = querySnapshot.docs.map((doc) => ({
          id: doc.id,
          quest: doc.data(),
        }));
        dispatch({ type: 'SET_QUESTIONS', payload: questions });
      } catch (error) {
        console.error('Error fetching ACL questions:', error);
      }
    };

    fetchData();

    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        const userDetails = {
          uid: user.uid,
          email: user.email,
          displayName: user.displayName,
          photoURL: user.photoURL,
        };
        dispatch({ type: 'SET_USER', payload: userDetails });
      } else {
        dispatch({ type: 'SET_USER', payload: null });
      }
    });

    return () => unsubscribe();
  }, []);

  return (
    <StoreContext.Provider value={{ state, dispatch }}>
      {children}
    </StoreContext.Provider>
  );
};

export const useStore = () => useContext(StoreContext);
