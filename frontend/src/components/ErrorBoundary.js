import React from 'react';
import { Box, Typography, Button, Card, CardContent } from '@mui/material';
import { ErrorOutline as ErrorIcon, Refresh as RefreshIcon } from '@mui/icons-material';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{
          minHeight: '100vh', display: 'flex', alignItems: 'center',
          justifyContent: 'center', bgcolor: 'background.default', p: 3
        }}>
          <Card sx={{ maxWidth: 500, textAlign: 'center' }}>
            <CardContent sx={{ p: 4 }}>
              <ErrorIcon sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom fontWeight={700}>
                Something went wrong
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                An unexpected error occurred. This has been logged for review.
                Please refresh the page to continue.
              </Typography>
              <Typography variant="caption" sx={{
                display: 'block', mb: 3, p: 1.5, bgcolor: 'action.hover',
                borderRadius: 1, fontFamily: 'monospace', color: 'text.secondary'
              }}>
                {this.state.error?.message || 'Unknown error'}
              </Typography>
              <Button variant="contained" startIcon={<RefreshIcon />}
                onClick={() => window.location.reload()}
                sx={{ background: 'linear-gradient(135deg, #0d47a1, #1565c0)' }}>
                Refresh Page
              </Button>
            </CardContent>
          </Card>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
