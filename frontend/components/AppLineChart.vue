<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  CategoryScale,
  Chart,
  Filler,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, LineController, Tooltip, Legend, Filler)

interface LineChartDataset {
  label: string
  data: number[]
  borderColor: string
  backgroundColor?: string
  yAxisID?: 'y' | 'y1'
}
const props = withDefaults(
  defineProps<{
    labels: string[]
    datasets: LineChartDataset[]
    height?: number
  }>(),
  { height: 240 },
)

const canvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

function hasSecondAxis(): boolean {
  return props.datasets.some((dataset) => dataset.yAxisID === 'y1')
}

function buildData() {
  return {
    labels: [...props.labels],
    datasets: props.datasets.map((dataset) => ({
      label: dataset.label,
      data: dataset.data,
      borderColor: dataset.borderColor,
      backgroundColor: dataset.backgroundColor ?? dataset.borderColor,
      yAxisID: dataset.yAxisID ?? 'y',
      borderWidth: 2,
      pointRadius: 2,
      pointHoverRadius: 4,
      tension: 0.25,
      fill: Boolean(dataset.backgroundColor),
    })),
  }
}

function buildChart() {
  if (!canvas.value) return
  chart = new Chart(canvas.value, {
    type: 'line',
    data: buildData(),
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: props.datasets.length > 1,
          position: 'top',
          labels: { boxWidth: 12, boxHeight: 12, usePointStyle: true },
        },
      },
      scales: {
        x: { ticks: { maxTicksLimit: 10 } },
        y: { beginAtZero: true },
        ...(hasSecondAxis()
          ? { y1: { beginAtZero: true, position: 'right' as const, grid: { drawOnChartArea: false } } }
          : {}),
      },
    },
  })
}

function updateChart() {
  if (!chart) return
  chart.data = buildData()
  chart.update()
}

onMounted(buildChart)

watch(
  () => ({ labels: props.labels, datasets: props.datasets }),
  () => updateChart(),
  { deep: true },
)

onBeforeUnmount(() => {
  chart?.destroy()
  chart = null
})
</script>

<template>
  <div class="relative" :style="{ height: `${height}px` }">
    <canvas ref="canvas"></canvas>
  </div>
</template>
