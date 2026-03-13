'use client';

import { useState, useEffect } from 'react';
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
  // State for user-selected chart type (defaults to AI recommendation)
  const [selectedChartType, setSelectedChartType] = useState(chartType);

  // Update when chartType prop changes (new query executed)
  useEffect(() => {
    setSelectedChartType(chartType);
  }, [chartType]);

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

  // Generate vibrant colors specifically for pie charts
  const generatePieColors = (count: number) => {
    const colors = [
      'rgba(99, 102, 241, 0.9)',   // Indigo
      'rgba(59, 130, 246, 0.9)',   // Blue
      'rgba(16, 185, 129, 0.9)',   // Green
      'rgba(245, 158, 11, 0.9)',   // Amber
      'rgba(239, 68, 68, 0.9)',    // Red
      'rgba(168, 85, 247, 0.9)',   // Purple
      'rgba(236, 72, 153, 0.9)',   // Pink
      'rgba(14, 165, 233, 0.9)',   // Sky
      'rgba(34, 197, 94, 0.9)',    // Emerald
      'rgba(234, 88, 12, 0.9)',    // Orange
    ];
    return colors.slice(0, count);
  };

  const chartData = {
    labels: data.labels || [],
    datasets: (data.datasets || []).map((dataset, idx) => ({
      label: dataset.label,
      data: dataset.data,
      backgroundColor: selectedChartType === 'pie' 
        ? data.labels.map((_, i) => generatePieColors(data.labels.length)[i])
        : generateColors(data.datasets.length)[idx],
      borderColor: selectedChartType === 'pie'
        ? data.labels.map((_, i) => generatePieColors(data.labels.length)[i].replace('0.9', '1'))
        : generateColors(data.datasets.length)[idx].replace('0.8', '1'),
      borderWidth: selectedChartType === 'pie' ? 3 : 2,
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
            size: 14,
          },
          padding: 15,
        },
      },
      title: {
        display: !!config.title,
        text: config.title || '',
        font: {
          size: 18,
          weight: 'bold',
        },
        padding: {
          bottom: 20,
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

  const pieOptions: ChartOptions<'pie'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          font: {
            size: 16,
          },
          padding: 20,
          boxWidth: 20,
          boxHeight: 20,
        },
      },
      title: {
        display: !!config.title,
        text: config.title || '',
        font: {
          size: 20,
          weight: 'bold',
        },
        padding: {
          bottom: 30,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 16,
        titleFont: {
          size: 16,
        },
        bodyFont: {
          size: 15,
        },
        callbacks: {
          label: (context) => {
            const label = context.label || '';
            const value = context.parsed;
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: ${value} (${percentage}%)`;
          },
        },
      },
    },
  };

  const renderChart = () => {
    switch (selectedChartType) {
      case 'bar':
        return (
          <div className="h-[450px]">
            <Bar data={chartData} options={barLineOptions} />
          </div>
        );
      case 'line':
        return (
          <div className="h-[450px]">
            <Line data={chartData} options={barLineOptions} />
          </div>
        );
      case 'pie':
        return (
          <div className="h-[600px] flex items-center justify-center">
            <div className="w-full px-8">
              <Pie data={chartData} options={pieOptions} />
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
            Unsupported chart type: {selectedChartType}
          </div>
        );
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-10 shadow-sm max-w-full">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xl font-semibold text-gray-900">
            Data Visualization
          </h4>
          <span className="text-xs font-medium text-gray-600 bg-gray-100 px-3 py-1.5 rounded-full">
            {chartType.toUpperCase()} RECOMMENDED
          </span>
        </div>
        {config.description && (
          <p className="text-sm text-gray-600 mt-2">{config.description}</p>
        )}
        
        {/* Chart Type Toggle */}
        <div className="mt-4 flex items-center gap-2">
          <span className="text-sm text-gray-600 font-medium">View as:</span>
          <div className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-1">
            <button
              onClick={() => setSelectedChartType('bar')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${
                selectedChartType === 'bar'
                  ? 'bg-white text-indigo-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
               Bar
            </button>
            <button
              onClick={() => setSelectedChartType('pie')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${
                selectedChartType === 'pie'
                  ? 'bg-white text-indigo-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
               Pie
            </button>
            <button
              onClick={() => setSelectedChartType('line')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${
                selectedChartType === 'line'
                  ? 'bg-white text-indigo-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
               Line
            </button>
          </div>
          {selectedChartType !== chartType && (
            <span className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
              Custom view
            </span>
          )}
        </div>
      </div>
      
      {renderChart()}
      
    </div>
  );
}
