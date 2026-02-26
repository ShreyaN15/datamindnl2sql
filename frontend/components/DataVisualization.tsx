'use client';

import { useEffect, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';
import { Bar, Line, Pie, Scatter } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface VisualizationData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
  }>;
}

interface ChartConfig {
  title?: string;
  x_label?: string;
  y_label?: string;
  description?: string;
  horizontal?: boolean;
}

interface DataVisualizationProps {
  chartType: string;
  data: VisualizationData;
  config: ChartConfig;
}

export default function DataVisualization({ chartType, data, config }: DataVisualizationProps) {
  // Defensive check: ensure data is valid
  if (!data || !data.labels || !data.datasets || !Array.isArray(data.datasets)) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-red-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div>
            <h4 className="font-semibold text-red-900 mb-1">Visualization Error</h4>
            <p className="text-sm text-red-800">Invalid or missing data for visualization</p>
          </div>
        </div>
      </div>
    );
  }

  // Generate random colors for datasets
  const generateColors = (count: number) => {
    const colors = [
      'rgba(99, 102, 241, 0.8)',   // Indigo
      'rgba(59, 130, 246, 0.8)',   // Blue
      'rgba(16, 185, 129, 0.8)',   // Green
      'rgba(245, 158, 11, 0.8)',   // Amber
      'rgba(239, 68, 68, 0.8)',    // Red
      'rgba(168, 85, 247, 0.8)',   // Purple
      'rgba(236, 72, 153, 0.8)',   // Pink
    ];
    return colors.slice(0, count);
  };

  const chartData = {
    labels: data.labels || [],
    datasets: (data.datasets || []).map((dataset, idx) => ({
      label: dataset.label,
      data: dataset.data,
      backgroundColor: chartType === 'pie' 
        ? data.labels.map((_, i) => generateColors(data.labels.length)[i])
        : generateColors(data.datasets.length)[idx],
      borderColor: chartType === 'pie'
        ? data.labels.map((_, i) => generateColors(data.labels.length)[i].replace('0.8', '1'))
        : generateColors(data.datasets.length)[idx].replace('0.8', '1'),
      borderWidth: 2,
    })),
  };

  const commonOptions: ChartOptions<any> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          font: {
            size: 12,
          },
        },
      },
      title: {
        display: !!config.title,
        text: config.title || '',
        font: {
          size: 16,
          weight: 'bold',
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        titleFont: {
          size: 14,
        },
        bodyFont: {
          size: 13,
        },
      },
    },
  };

  const barLineOptions: ChartOptions<'bar' | 'line'> = {
    ...commonOptions,
    scales: {
      x: {
        title: {
          display: !!config.x_label,
          text: config.x_label || '',
          font: {
            size: 12,
            weight: 'bold',
          },
        },
        ticks: {
          maxRotation: 45,
          minRotation: 0,
        },
      },
      y: {
        title: {
          display: !!config.y_label,
          text: config.y_label || '',
          font: {
            size: 12,
            weight: 'bold',
          },
        },
        beginAtZero: true,
      },
    },
    indexAxis: config.horizontal ? 'y' as const : 'x' as const,
  };

  const renderChart = () => {
    switch (chartType) {
      case 'bar':
        return (
          <div className="h-96">
            <Bar data={chartData} options={barLineOptions} />
          </div>
        );
      case 'line':
        return (
          <div className="h-96">
            <Line data={chartData} options={barLineOptions} />
          </div>
        );
      case 'pie':
        return (
          <div className="h-96 flex items-center justify-center">
            <div className="w-full max-w-md">
              <Pie data={chartData} options={commonOptions} />
            </div>
          </div>
        );
      case 'scatter':
        return (
          <div className="h-96">
            <Scatter 
              data={{
                datasets: data.datasets.map((dataset, idx) => ({
                  label: dataset.label,
                  data: dataset.data.map((val, i) => ({
                    x: i,
                    y: val,
                  })),
                  backgroundColor: generateColors(data.datasets.length)[idx],
                })),
              }} 
              options={barLineOptions} 
            />
          </div>
        );
      default:
        return (
          <div className="text-center py-8 text-gray-500">
            Unsupported chart type: {chartType}
          </div>
        );
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-semibold text-gray-900">
            Data Visualization
          </h4>
          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
            {chartType.toUpperCase()} CHART
          </span>
        </div>
        {config.description && (
          <p className="text-sm text-gray-600">{config.description}</p>
        )}
      </div>
      
      {renderChart()}
      
      <div className="mt-4 text-xs text-gray-500 text-center">
        Powered by Chart.js • Interactive chart
      </div>
    </div>
  );
}
