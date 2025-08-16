'use client';

import React from 'react';
import { Container, Box } from '@mui/material';
import { WorkItemManager } from '../../components/work-items';

export default function WorkItemsPage() {
  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        <WorkItemManager
          title="Work Items Management"
          showCreateButton={true}
          initialView="list"
        />
      </Box>
    </Container>
  );
}