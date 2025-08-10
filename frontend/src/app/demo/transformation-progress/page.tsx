// ABOUTME: Demo page for transformation progress component
// ABOUTME: Shows the component with simulated real-time updates

'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { TransformationProgress } from '@/components/study/transformation-progress';
import { generateMockExecution, simulateProgress } from '@/lib/mock/transformation-progress-mock';
import { useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Play, RotateCcw } from 'lucide-react';

export default function TransformationProgressDemo() {
  const [isRunning, setIsRunning] = useState(false);
  const [execution, setExecution] = useState(() => generateMockExecution('demo-study'));
  const queryClient = useQueryClient();

  const startSimulation = () => {
    const newExecution = generateMockExecution('demo-study');
    setExecution(newExecution);
    setIsRunning(true);

    // Mock the query data
    queryClient.setQueryData(
      ['pipeline-execution', 'demo-study', newExecution.id],
      newExecution
    );

    const cleanup = simulateProgress(newExecution, (updated) => {
      setExecution(updated);
      queryClient.setQueryData(
        ['pipeline-execution', 'demo-study', updated.id],
        updated
      );
      
      if (updated.status === 'success' || updated.status === 'failed') {
        setIsRunning(false);
      }
    });

    // Store cleanup function
    (window as any).__simulationCleanup = cleanup;
  };

  const resetSimulation = () => {
    // Cleanup previous simulation
    if ((window as any).__simulationCleanup) {
      (window as any).__simulationCleanup();
    }
    
    const newExecution = generateMockExecution('demo-study');
    setExecution(newExecution);
    setIsRunning(false);
    
    queryClient.setQueryData(
      ['pipeline-execution', 'demo-study', newExecution.id],
      newExecution
    );
  };

  useEffect(() => {
    // Set initial query data
    queryClient.setQueryData(
      ['pipeline-execution', 'demo-study', execution.id],
      execution
    );

    return () => {
      // Cleanup on unmount
      if ((window as any).__simulationCleanup) {
        (window as any).__simulationCleanup();
      }
    };
  }, []);

  return (
    <div className="container mx-auto py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Transformation Progress Demo</h1>
        <p className="text-muted-foreground mt-1">
          Demonstrates the real-time pipeline execution progress tracking component
        </p>
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-8">
          <TransformationProgress
            studyId="demo-study"
            executionId={execution.id}
            onComplete={() => {
              console.log('Execution completed!');
            }}
          />
        </div>

        <div className="col-span-4">
          <Card>
            <CardHeader>
              <CardTitle>Demo Controls</CardTitle>
              <CardDescription>
                Simulate pipeline execution progress
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button
                className="w-full"
                onClick={startSimulation}
                disabled={isRunning}
              >
                <Play className="mr-2 h-4 w-4" />
                Start Simulation
              </Button>
              
              <Button
                variant="outline"
                className="w-full"
                onClick={resetSimulation}
              >
                <RotateCcw className="mr-2 h-4 w-4" />
                Reset
              </Button>

              <div className="pt-4 border-t">
                <h4 className="text-sm font-medium mb-2">About this Demo</h4>
                <p className="text-sm text-muted-foreground">
                  This demo simulates a pipeline execution with multiple steps:
                </p>
                <ul className="text-sm text-muted-foreground mt-2 space-y-1">
                  <li>• Real-time progress updates</li>
                  <li>• Success and failure scenarios</li>
                  <li>• Log streaming</li>
                  <li>• Retry capabilities</li>
                  <li>• Execution summaries</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}