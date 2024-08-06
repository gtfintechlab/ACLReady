import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
import { getAuth} from 'firebase/auth';

const firebaseConfig = {
  apiKey: "AIzaSyDMIFVBP8GIIqnwD3_mrfYXO7K8cui-el4",
  authDomain: "aclready.firebaseapp.com",
  projectId: "aclready",
  storageBucket: "aclready.appspot.com",
  messagingSenderId: "284444316027",
  appId: "1:284444316027:web:d4813eefd78de575f5adde",
  measurementId: "G-DYGWH1LQ4R"
};

const app = initializeApp(firebaseConfig)

export const auth = getAuth()

export default getFirestore(app);