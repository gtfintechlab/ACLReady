import React, { useState } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import db, { auth } from '../../firebase';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword, signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import { doc, getDoc, setDoc } from 'firebase/firestore';

export default function AuthModal({ open, onClose }) {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');

  const toggleSignUp = () => {
    setIsSignUp(!isSignUp);
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    try {
      if (isSignUp) {
        await createUserWithEmailAndPassword(auth, email, password);
        await setDoc(doc(db, "users", email), {
            name: fullName,
            email: email
          });
      } else {
        await signInWithEmailAndPassword(auth, email, password);
      }
      setEmail("");
      setPassword("");
      setFullName("");
      onClose();
    } catch (error) {
      console.error('Authentication error:', error);
    }
  };

  const handleGoogleSignIn = async () => {
    const provider = new GoogleAuthProvider();
    try {
      const result = await signInWithPopup(auth, provider);
      const docRef = doc(db, "users", result.user.email);
      const docSnap = await getDoc(docRef);
        if(!docSnap.exists()) {
            setDoc(doc(db, "users", result.user.email), {
                name: result.user.displayName,
                email: result.user.email,
              });
        }
      onClose();
    } catch (error) {
      console.error('Google sign-in error:', error);
    }
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>{isSignUp ? 'Sign Up' : 'Log In'} to ACLReady</DialogTitle>
      <DialogContent>
        <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {isSignUp && (
            <TextField
              label="Full Name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              fullWidth
            />
          )}
          <TextField
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            fullWidth
            required
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            fullWidth
            required
          />
          <Button type="submit" variant="contained" color="primary" fullWidth>
            {isSignUp ? 'Sign Up' : 'Log In'}
          </Button>
          <Button onClick={handleGoogleSignIn} variant="outlined" color="primary" fullWidth>
            Sign in with Google
          </Button>
        </form>
        <Typography align="center" style={{ marginTop: '1rem' }}>
          {isSignUp ? 'Already have an account?' : "Don't have an account?"}
          <Button onClick={toggleSignUp} color="primary">
            {isSignUp ? 'Log In' : 'Sign Up'}
          </Button>
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="secondary">
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
}
