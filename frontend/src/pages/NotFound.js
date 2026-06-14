import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Button, Card, CardContent } from '@mui/material';
import { ErrorOutline as ErrorIcon, Home as HomeIcon } from '@mui/icons-material';

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <Box sx={{
      minHeight: '100vh', display: 'flex', alignItems: 'center',
      justifyContent: 'center', bgcolor: 'background.default', p: 3
    }}>
      <Card sx={{ maxWidth: 500, textAlign: 'center', borderRadius: 4 }} className="fade-slide-up">
        <CardContent sx={{ p: 5 }}>
          <ErrorIcon sx={{ fontSize: 72, color: 'primary.main', mb: 2 }} />
          <Typography variant="h3" gutterBottom fontWeight={800}>
            404
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
            Page Not Found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
            The page you are looking for does not exist or has been moved.
          </Typography>
          <Button
            variant="contained" size="large" startIcon={<HomeIcon />}
            onClick={() => navigate('/')}
            sx={{ background: 'linear-gradient(135deg, #0d47a1, #1565c0)', px: 4 }}
          >
            Back to Dashboard
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
};

export default NotFound;
