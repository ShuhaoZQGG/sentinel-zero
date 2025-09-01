import React from 'react';
import { Container, Grid, Paper, Typography } from '@mui/material';

const Dashboard: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Typography variant="h4" gutterBottom>
            Dashboard
          </Typography>
        </Grid>
        <Grid item xs={12} md={8} lg={9}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Process List</Typography>
            <Typography>Processes will be displayed here</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4} lg={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">System Metrics</Typography>
            <Typography>Metrics will be displayed here</Typography>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;