import React from 'react';
import { Box, Button, Container, TextField, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
  const navigate = useNavigate();

  const handleLogin = () => {
    // Simplified login for MVP
    localStorage.setItem('token', 'mock-token');
    navigate('/');
  };

  return (
    <Container component="main" maxWidth="xs">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Typography component="h1" variant="h5">
          SentinelZero Login
        </Typography>
        <Box sx={{ mt: 1 }}>
          <TextField margin="normal" required fullWidth label="Username" autoFocus />
          <TextField margin="normal" required fullWidth label="Password" type="password" />
          <Button fullWidth variant="contained" sx={{ mt: 3, mb: 2 }} onClick={handleLogin}>
            Sign In
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default Login;