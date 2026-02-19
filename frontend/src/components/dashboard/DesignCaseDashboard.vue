<template>
  <div class="design-case-dashboard">

    <!-- Section 1: Summary Table -->
    <section class="dashboard-section summary-section">
      <h3>Design Case Summary</h3>
      <div class="table-wrapper">
        <table class="summary-table">
          <thead>
            <tr>
              <th class="col-color"></th>
              <th
                class="col-name sortable"
                @click="toggleSort('name')"
              >
                Name
                <span v-if="sortColumn === 'name'" class="sort-icon">
                  {{ sortDirection === 'asc' ? '\u25B2' : '\u25BC' }}
                </span>
              </th>
              <th
                v-for="axis in axisDefs"
                :key="axis.id"
                class="col-metric sortable"
                @click="toggleSort(axis.id)"
              >
                {{ axis.label }}
                <span v-if="axis.unit" class="unit">({{ axis.unit }})</span>
                <span v-if="sortColumn === axis.id" class="sort-icon">
                  {{ sortDirection === 'asc' ? '\u25B2' : '\u25BC' }}
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="dc in sortedDesignCases"
              :key="dc.id"
              :class="{
                highlighted: highlightedCaseId === dc.id,
                filtered: !filteredCaseIds.has(dc.id)
              }"
              @mouseenter="highlightedCaseId = dc.id"
              @mouseleave="highlightedCaseId = null"
            >
              <td class="col-color">
                <div class="color-swatch" :style="{ background: dc.color }"></div>
              </td>
              <td class="col-name">{{ dc.name }}</td>
              <td
                v-for="axis in axisDefs"
                :key="axis.id"
                :class="{ 'best-value': isBestValue(dc, axis) }"
              >
                {{ formatAxisValue(dc, axis) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Section 2: Parallel Coordinates -->
    <section class="dashboard-section parallel-section">
      <h3>Parallel Coordinates</h3>
      <div ref="parallelContainer" class="parallel-svg-container"></div>
    </section>

    <!-- Section 3: Weighted Scoring -->
    <section class="dashboard-section scoring-section">
      <h3>Weighted Scoring</h3>
      <div class="scoring-layout">
        <div class="sliders-panel">
          <div v-for="axis in axisDefs" :key="axis.id" class="slider-row">
            <label :title="axis.label">{{ axis.label }}</label>
            <input
              type="range"
              min="0"
              max="100"
              step="1"
              :value="weights[axis.id] ?? 50"
              class="weight-slider"
              @input="(e) => weights[axis.id] = Number((e.target as HTMLInputElement).value)"
            />
            <span class="weight-value">{{ weights[axis.id] ?? 50 }}</span>
          </div>
        </div>
        <div class="ranking-panel">
          <TransitionGroup name="rank-list" tag="div" class="ranking-list">
            <div
              v-for="(entry, index) in compositeScores"
              :key="entry.caseId"
              class="rank-bar-row"
              :class="{
                highlighted: highlightedCaseId === entry.caseId,
                filtered: !filteredCaseIds.has(entry.caseId)
              }"
              @mouseenter="highlightedCaseId = entry.caseId"
              @mouseleave="highlightedCaseId = null"
            >
              <span class="rank-number">{{ index + 1 }}</span>
              <div class="rank-color-swatch" :style="{ background: getCaseColor(entry.caseId) }"></div>
              <span class="rank-name">{{ getCaseName(entry.caseId) }}</span>
              <div class="rank-bar-wrapper">
                <div
                  class="rank-bar-fill"
                  :style="{
                    width: `${entry.score * 100}%`,
                    background: getCaseColor(entry.caseId)
                  }"
                ></div>
              </div>
              <span class="rank-score">{{ (entry.score * 100).toFixed(1) }}</span>
            </div>
          </TransitionGroup>
        </div>
      </div>
    </section>

    <!-- Section 4: Matrix Comparison -->
    <section class="dashboard-section matrix-section">
      <h3>Matrix Comparison</h3>

      <div class="matrix-controls">
        <div class="control-row">
          <label>Matrix:</label>
          <select v-model="matrixType" class="matrix-select">
            <option value="cos_theta">cos &theta;</option>
            <option value="inner_product">Inner Product</option>
            <option value="energy">Energy</option>
          </select>
          <label>Baseline:</label>
          <select v-model="baselineCaseId" class="matrix-select">
            <option value="">Select baseline...</option>
            <option v-for="dc in designCases" :key="dc.id" :value="dc.id">
              {{ dc.name }}
            </option>
          </select>
          <button
            class="load-matrix-btn"
            :disabled="matrixLoading || designCases.length === 0"
            @click="loadAllMatrices"
          >
            {{ matrixLoading ? 'Loading...' : 'Load Matrices' }}
          </button>
        </div>
      </div>

      <!-- Cell-level comparison bar chart -->
      <div v-if="selectedCell" class="cell-comparison">
        <h4>
          {{ selectedCell.perfIName }} vs {{ selectedCell.perfJName }}
          <span class="cell-comparison-subtitle">{{ matrixTypeLabel }} across all design cases</span>
        </h4>
        <div class="cell-bars">
          <div
            v-for="entry in cellComparisonData"
            :key="entry.caseId"
            class="cell-bar-row"
            :class="{ highlighted: highlightedCaseId === entry.caseId }"
            @mouseenter="highlightedCaseId = entry.caseId"
            @mouseleave="highlightedCaseId = null"
          >
            <div class="cell-bar-color" :style="{ background: entry.color }"></div>
            <span class="cell-bar-name">{{ entry.name }}</span>
            <div class="cell-bar-track">
              <div
                class="cell-bar-fill"
                :class="{ negative: entry.value < 0 }"
                :style="cellBarStyle(entry.value)"
              ></div>
              <div class="cell-bar-zero"></div>
            </div>
            <span class="cell-bar-value" :class="{ negative: entry.value < 0 }">
              {{ formatCellValue(entry.value) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Baseline diff matrices -->
      <div v-if="baselineCaseId && currentMatrixMap[baselineCaseId]" class="baseline-diff-area">
        <div class="baseline-info">
          Baseline: <strong>{{ getCaseName(baselineCaseId) }}</strong>
        </div>
        <div class="diff-grid">
          <div
            v-for="dc in nonBaselineCases"
            :key="dc.id"
            class="diff-card"
            :class="{ highlighted: highlightedCaseId === dc.id }"
            @mouseenter="highlightedCaseId = dc.id"
            @mouseleave="highlightedCaseId = null"
          >
            <div class="diff-card-header">
              <div class="diff-card-color" :style="{ background: dc.color }"></div>
              <span>{{ dc.name }}</span>
            </div>
            <div class="diff-matrix-wrapper" v-if="currentMatrixMap[dc.id]">
              <table class="mini-matrix">
                <thead>
                  <tr>
                    <th></th>
                    <th
                      v-for="(label, j) in matrixLabels"
                      :key="j"
                      :title="label"
                    >{{ truncLabel(label) }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in getDiffMatrix(dc.id)" :key="i">
                    <th :title="matrixLabels[i]">{{ truncLabel(matrixLabels[i]) }}</th>
                    <td
                      v-for="(val, j) in row"
                      :key="j"
                      :style="diffCellStyle(val, i, j)"
                      :class="{ diagonal: i === j }"
                      @click="selectMatrixCell(i, j)"
                      class="clickable-cell"
                    >
                      {{ i === j ? '-' : formatDiff(val) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="diff-matrix-loading">
              Loading...
            </div>
          </div>
        </div>
      </div>

      <!-- No baseline: show individual matrices with clickable cells -->
      <div v-else-if="Object.keys(currentMatrixMap).length > 0" class="individual-matrices">
        <div class="diff-grid">
          <div
            v-for="dc in designCases"
            :key="dc.id"
            class="diff-card"
            :class="{ highlighted: highlightedCaseId === dc.id }"
            @mouseenter="highlightedCaseId = dc.id"
            @mouseleave="highlightedCaseId = null"
          >
            <div class="diff-card-header">
              <div class="diff-card-color" :style="{ background: dc.color }"></div>
              <span>{{ dc.name }}</span>
            </div>
            <div class="diff-matrix-wrapper" v-if="currentMatrixMap[dc.id]">
              <table class="mini-matrix">
                <thead>
                  <tr>
                    <th></th>
                    <th
                      v-for="(label, j) in matrixLabels"
                      :key="j"
                      :title="label"
                    >{{ truncLabel(label) }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in currentMatrixMap[dc.id]" :key="i">
                    <th :title="matrixLabels[i]">{{ truncLabel(matrixLabels[i]) }}</th>
                    <td
                      v-for="(val, j) in row"
                      :key="j"
                      :style="matrixCellStyle(val, i, j)"
                      :class="{ diagonal: i === j }"
                      @click="selectMatrixCell(i, j)"
                      class="clickable-cell"
                    >
                      {{ i === j ? diagonalLabel : formatMatrixValue(val) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="matrix-placeholder">
        <p>Click "Load Matrices" to fetch matrices for all design cases</p>
      </div>
    </section>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as d3 from 'd3'
import type { DesignCase, Performance } from '../../types/project'
import { formatEnergy } from '../../utils/energyFormat'
import { structuralTradeoffApi } from '../../utils/api'

const props = defineProps<{
  projectId: string
  designCases: DesignCase[]
  performances: Performance[]
}>()

// =====================
// Shared cross-link state
// =====================
const highlightedCaseId = ref<string | null>(null)

// =====================
// Common data definitions
// =====================
interface AxisDef {
  id: string
  label: string
  unit: string
  lowerIsBetter: boolean
  getValue: (dc: DesignCase) => number | null
}

const leafPerformances = computed(() =>
  props.performances.filter(p => p.is_leaf)
)

const axisDefs = computed<AxisDef[]>(() => {
  const axes: AxisDef[] = [
    {
      id: '__height',
      label: 'Height',
      unit: '',
      lowerIsBetter: false,
      getValue: (dc) => dc.mountain_position?.H ?? null
    },
    {
      id: '__energy',
      label: 'Energy',
      unit: 'E',
      lowerIsBetter: true,
      getValue: (dc) => dc.energy?.total_energy ?? null
    }
  ]
  for (const perf of leafPerformances.value) {
    axes.push({
      id: perf.id,
      label: perf.name,
      unit: perf.unit || '',
      lowerIsBetter: false,
      getValue: (dc) => {
        const val = dc.performance_values[perf.id]
        if (typeof val === 'number') return val
        if (typeof val === 'string') {
          const n = parseFloat(val)
          return isNaN(n) ? null : n
        }
        return null
      }
    })
  }
  return axes
})

// =====================
// Section 1: Summary Table
// =====================
const sortColumn = ref<string>('name')
const sortDirection = ref<'asc' | 'desc'>('asc')

function toggleSort(columnId: string) {
  if (sortColumn.value === columnId) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = columnId
    sortDirection.value = 'asc'
  }
}

const sortedDesignCases = computed(() => {
  const cases = [...props.designCases]
  const axis = axisDefs.value.find(a => a.id === sortColumn.value)

  cases.sort((a, b) => {
    if (sortColumn.value === 'name') {
      const cmp = a.name.localeCompare(b.name)
      return sortDirection.value === 'asc' ? cmp : -cmp
    }
    if (!axis) return 0
    const va = axis.getValue(a) ?? -Infinity
    const vb = axis.getValue(b) ?? -Infinity
    return sortDirection.value === 'asc' ? va - vb : vb - va
  })
  return cases
})

const bestValues = computed(() => {
  const result: { [axisId: string]: { value: number; caseIds: Set<string> } } = {}
  for (const axis of axisDefs.value) {
    let best = axis.lowerIsBetter ? Infinity : -Infinity
    const caseIds = new Set<string>()
    for (const dc of props.designCases) {
      const val = axis.getValue(dc)
      if (val === null) continue
      const isBetter = axis.lowerIsBetter ? val < best : val > best
      if (isBetter) {
        best = val
        caseIds.clear()
        caseIds.add(dc.id)
      } else if (val === best) {
        caseIds.add(dc.id)
      }
    }
    if (caseIds.size > 0) result[axis.id] = { value: best, caseIds }
  }
  return result
})

function isBestValue(dc: DesignCase, axis: AxisDef): boolean {
  return bestValues.value[axis.id]?.caseIds.has(dc.id) ?? false
}

function formatAxisValue(dc: DesignCase, axis: AxisDef): string {
  const val = axis.getValue(dc)
  if (val === null) return '-'
  if (axis.id === '__energy') return formatEnergy(val, 2)
  return typeof val === 'number' ? val.toFixed(3) : String(val)
}

// =====================
// Section 2: Parallel Coordinates (D3)
// =====================
const parallelContainer = ref<HTMLElement | null>(null)
const brushRanges = ref<Map<string, [number, number]>>(new Map())

const filteredCaseIds = computed(() => {
  if (brushRanges.value.size === 0) {
    return new Set(props.designCases.map(dc => dc.id))
  }
  const passing = new Set<string>()
  for (const dc of props.designCases) {
    let pass = true
    for (const [axisId, [lo, hi]] of brushRanges.value.entries()) {
      const axis = axisDefs.value.find(a => a.id === axisId)
      if (!axis) continue
      const val = axis.getValue(dc)
      if (val === null || val < lo || val > hi) {
        pass = false
        break
      }
    }
    if (pass) passing.add(dc.id)
  }
  return passing
})

function renderParallelCoordinates() {
  if (!parallelContainer.value || props.designCases.length === 0) return

  const container = parallelContainer.value
  container.innerHTML = ''

  const rect = container.getBoundingClientRect()
  const width = rect.width || 900
  const height = rect.height || 350
  const margin = { top: 40, right: 40, bottom: 20, left: 40 }
  const innerW = width - margin.left - margin.right
  const innerH = height - margin.top - margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('viewBox', `0 0 ${width} ${height}`)
    .attr('preserveAspectRatio', 'xMidYMid meet')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const axes = axisDefs.value.map(a => a.id)

  const xScale = d3.scalePoint<string>()
    .domain(axes)
    .range([0, innerW])
    .padding(0.05)

  const yScales: { [id: string]: d3.ScaleLinear<number, number> } = {}
  for (const axisId of axes) {
    const axisDef = axisDefs.value.find(a => a.id === axisId)
    if (!axisDef) continue
    const vals = props.designCases
      .map(dc => axisDef.getValue(dc))
      .filter((v): v is number => v !== null)
    const min = d3.min(vals) ?? 0
    const max = d3.max(vals) ?? 1
    const padding = (max - min) * 0.08 || 0.5
    yScales[axisId] = d3.scaleLinear()
      .domain([min - padding, max + padding])
      .range([innerH, 0])
  }

  const lineGroup = g.append('g').attr('class', 'lines')

  for (const dc of props.designCases) {
    const points: [number, number][] = []
    for (const axisId of axes) {
      const axisDef = axisDefs.value.find(a => a.id === axisId)
      if (!axisDef) continue
      const val = axisDef.getValue(dc)
      if (val === null) continue
      const x = xScale(axisId) ?? 0
      const y = yScales[axisId]?.(val) ?? 0
      points.push([x, y])
    }

    if (points.length < 2) continue

    lineGroup.append('path')
      .attr('class', 'case-line')
      .attr('d', d3.line()(points) || '')
      .attr('fill', 'none')
      .attr('stroke', dc.color || '#635d73')
      .attr('stroke-width', 2.5)
      .attr('stroke-opacity', 0.7)
      .attr('data-case-id', dc.id)
      .style('cursor', 'pointer')
      .on('mouseenter', function () {
        highlightedCaseId.value = dc.id
      })
      .on('mouseleave', function () {
        highlightedCaseId.value = null
      })
  }

  const axisGroups = g.selectAll<SVGGElement, string>('.axis-group')
    .data(axes)
    .enter()
    .append('g')
    .attr('class', 'axis-group')
    .attr('transform', d => `translate(${xScale(d)}, 0)`)

  axisGroups.each(function (axisId: string) {
    const yScale = yScales[axisId]
    if (!yScale) return
    const axisGen = d3.axisLeft(yScale).ticks(5).tickSize(-6)
    const axisEl = d3.select(this).call(axisGen)
    axisEl.selectAll('text').attr('fill', '#b0b0b0').attr('font-size', '10px')
    axisEl.selectAll('line').attr('stroke', '#555')
    axisEl.select('.domain').attr('stroke', '#777')
  })

  axisGroups.append('text')
    .attr('y', -16)
    .attr('text-anchor', 'middle')
    .attr('fill', '#f3f3f3')
    .attr('font-size', '11px')
    .attr('font-weight', '600')
    .text(d => {
      const def = axisDefs.value.find(a => a.id === d)
      const label = def?.label || d
      return label.length > 12 ? label.substring(0, 11) + '...' : label
    })
    .append('title')
    .text(d => axisDefs.value.find(a => a.id === d)?.label || d)

  axisGroups.each(function (axisId: string) {
    const yScale = yScales[axisId]
    if (!yScale) return

    const brush = d3.brushY()
      .extent([[-14, 0], [14, innerH]])
      .on('brush end', (event: d3.D3BrushEvent<string>) => {
        if (!event.selection) {
          brushRanges.value.delete(axisId)
        } else {
          const [y0, y1] = event.selection as [number, number]
          brushRanges.value.set(axisId, [
            yScale.invert(y1),
            yScale.invert(y0)
          ])
        }
        brushRanges.value = new Map(brushRanges.value)
        updateLineStyles()
      })

    d3.select(this).append('g')
      .attr('class', 'brush')
      .call(brush)
  })

  updateLineStyles()
}

function updateLineStyles() {
  if (!parallelContainer.value) return
  const svg = d3.select(parallelContainer.value).select('svg')

  svg.selectAll<SVGPathElement, unknown>('.case-line')
    .attr('stroke-width', function () {
      const caseId = d3.select(this).attr('data-case-id')
      return caseId === highlightedCaseId.value ? 5 : 2.5
    })
    .attr('stroke-opacity', function () {
      const caseId = d3.select(this).attr('data-case-id')
      if (highlightedCaseId.value && caseId !== highlightedCaseId.value) return 0.12
      if (!filteredCaseIds.value.has(caseId)) return 0.08
      return 0.75
    })
    .each(function () {
      const caseId = d3.select(this).attr('data-case-id')
      if (caseId === highlightedCaseId.value) {
        ;(this as Element).parentNode?.appendChild(this as Node)
      }
    })
}

// =====================
// Section 3: Weighted Scoring
// =====================
const weights = ref<{ [axisId: string]: number }>({})

function initializeWeights() {
  const w: { [axisId: string]: number } = {}
  for (const axis of axisDefs.value) {
    w[axis.id] = weights.value[axis.id] ?? 50
  }
  weights.value = w
}

const normalizedValues = computed(() => {
  const result: { [caseId: string]: { [axisId: string]: number } } = {}

  for (const dc of props.designCases) {
    result[dc.id] = {}
  }

  for (const axis of axisDefs.value) {
    const vals = props.designCases
      .map(dc => axis.getValue(dc))
      .filter((v): v is number => v !== null)
    if (vals.length === 0) continue

    const min = Math.min(...vals)
    const max = Math.max(...vals)
    const range = max - min

    for (const dc of props.designCases) {
      const raw = axis.getValue(dc)
      let norm = raw !== null && range > 0
        ? (raw - min) / range
        : 0.5
      // Invert for lower-is-better axes (e.g. Energy)
      if (axis.lowerIsBetter) norm = 1 - norm
      result[dc.id][axis.id] = norm
    }
  }
  return result
})

const compositeScores = computed(() => {
  const totalWeight = Object.values(weights.value).reduce((sum, w) => sum + w, 0)
  if (totalWeight === 0) {
    return props.designCases.map(dc => ({ caseId: dc.id, score: 0 }))
  }

  return [...props.designCases]
    .map(dc => {
      let score = 0
      for (const axis of axisDefs.value) {
        const w = weights.value[axis.id] ?? 0
        const norm = normalizedValues.value[dc.id]?.[axis.id] ?? 0
        score += w * norm
      }
      return { caseId: dc.id, score: score / totalWeight }
    })
    .sort((a, b) => b.score - a.score)
})

// =====================
// Section 4: Matrix Comparison
// =====================
type MatrixType = 'cos_theta' | 'inner_product' | 'energy'

interface CaseMatrices {
  cos_theta: number[][]
  inner_product?: number[][]
  energy?: number[][]
}

const allMatricesMap = ref<{ [caseId: string]: CaseMatrices }>({})
const matrixLabels = ref<string[]>([])
const matrixLoading = ref(false)
const matrixType = ref<MatrixType>('cos_theta')
const baselineCaseId = ref<string>('')
const selectedCell = ref<{ i: number; j: number; perfIName: string; perfJName: string } | null>(null)

const matrixTypeLabel = computed(() => {
  switch (matrixType.value) {
    case 'cos_theta': return 'cos \u03B8'
    case 'inner_product': return 'Inner Product'
    case 'energy': return 'Energy'
  }
})

const diagonalLabel = computed(() => {
  switch (matrixType.value) {
    case 'cos_theta': return '1'
    case 'inner_product': return '-'
    case 'energy': return '-'
  }
})

const currentMatrixMap = computed<{ [caseId: string]: number[][] }>(() => {
  const result: { [caseId: string]: number[][] } = {}
  for (const [caseId, matrices] of Object.entries(allMatricesMap.value)) {
    const m = matrices[matrixType.value]
    if (m) result[caseId] = m
  }
  return result
})

const nonBaselineCases = computed(() =>
  props.designCases.filter(dc => dc.id !== baselineCaseId.value)
)

// Reset selected cell when matrix type changes
watch(matrixType, () => {
  selectedCell.value = null
})

async function loadAllMatrices() {
  if (props.designCases.length === 0) return
  matrixLoading.value = true

  try {
    const results = await Promise.all(
      props.designCases.map(dc =>
        structuralTradeoffApi.getForCase(props.projectId, dc.id)
          .then(res => ({ caseId: dc.id, data: res.data }))
          .catch(() => ({ caseId: dc.id, data: null }))
      )
    )

    const newMap: { [caseId: string]: CaseMatrices } = {}
    for (const r of results) {
      if (r.data?.cos_theta_matrix) {
        newMap[r.caseId] = {
          cos_theta: r.data.cos_theta_matrix,
          inner_product: r.data.inner_product_matrix || undefined,
          energy: r.data.energy_matrix || undefined
        }
        if (matrixLabels.value.length === 0 && r.data.performance_labels) {
          matrixLabels.value = r.data.performance_labels
        }
      }
    }
    allMatricesMap.value = newMap
  } catch (error) {
    console.error('Failed to load matrices:', error)
  } finally {
    matrixLoading.value = false
  }
}

function getDiffMatrix(caseId: string): number[][] {
  const baseline = currentMatrixMap.value[baselineCaseId.value]
  const target = currentMatrixMap.value[caseId]
  if (!baseline || !target) return []
  return target.map((row, i) =>
    row.map((val, j) => val - (baseline[i]?.[j] ?? 0))
  )
}

function selectMatrixCell(i: number, j: number) {
  if (i === j) return
  selectedCell.value = {
    i,
    j,
    perfIName: matrixLabels.value[i] || `P${i}`,
    perfJName: matrixLabels.value[j] || `P${j}`
  }
}

const cellComparisonData = computed(() => {
  if (!selectedCell.value) return []
  const { i, j } = selectedCell.value
  return props.designCases
    .filter(dc => currentMatrixMap.value[dc.id])
    .map(dc => ({
      caseId: dc.id,
      name: dc.name,
      color: dc.color,
      value: currentMatrixMap.value[dc.id][i]?.[j] ?? 0
    }))
    .sort((a, b) => b.value - a.value)
})

function cellBarStyle(value: number): Record<string, string> {
  if (matrixType.value === 'cos_theta') {
    // Fixed -1 to 1 range
    const absVal = Math.min(Math.abs(value), 1)
    const pct = absVal * 50
    if (value >= 0) {
      return { left: '50%', width: `${pct}%` }
    } else {
      return { left: `${50 - pct}%`, width: `${pct}%` }
    }
  }
  // Dynamic range for inner_product / energy
  const vals = cellComparisonData.value.map(e => e.value)
  const maxAbs = Math.max(...vals.map(v => Math.abs(v)), 1e-12)
  const absVal = Math.abs(value) / maxAbs
  const pct = absVal * 50
  if (value >= 0) {
    return { left: '50%', width: `${pct}%` }
  } else {
    return { left: `${50 - pct}%`, width: `${pct}%` }
  }
}

function matrixCellStyle(val: number, i: number, j: number): Record<string, string> {
  if (i === j) return {}
  if (matrixType.value === 'cos_theta') {
    const intensity = Math.min(Math.abs(val), 1)
    if (val < 0) {
      return { backgroundColor: `rgba(195, 102, 112, ${intensity * 0.8})` }
    }
    return { backgroundColor: `rgba(45, 144, 88, ${intensity * 0.8})` }
  }
  // For inner_product / energy: use dynamic range from all visible cells
  const matrix = currentMatrixMap.value
  let maxAbs = 0
  for (const caseId of Object.keys(matrix)) {
    const m = matrix[caseId]
    if (!m) continue
    for (let r = 0; r < m.length; r++) {
      for (let c = 0; c < m[r].length; c++) {
        if (r !== c) maxAbs = Math.max(maxAbs, Math.abs(m[r][c]))
      }
    }
  }
  if (maxAbs === 0) return {}
  const intensity = Math.min(Math.abs(val) / maxAbs, 1)
  if (val < 0) {
    return { backgroundColor: `rgba(195, 102, 112, ${intensity * 0.8})` }
  }
  return { backgroundColor: `rgba(45, 144, 88, ${intensity * 0.8})` }
}

function formatMatrixValue(val: number): string {
  if (matrixType.value === 'energy') {
    return formatEnergy(val, 2)
  }
  return val.toFixed(2)
}

function formatCellValue(val: number): string {
  if (matrixType.value === 'energy') {
    return formatEnergy(val, 3)
  }
  return val.toFixed(3)
}

function diffCellStyle(val: number, i: number, j: number): Record<string, string> {
  if (i === j) return {}
  const intensity = Math.min(Math.abs(val) * 2, 1)
  if (val > 0.01) {
    return { backgroundColor: `rgba(45, 144, 88, ${intensity})` }
  }
  if (val < -0.01) {
    return { backgroundColor: `rgba(195, 102, 112, ${intensity})` }
  }
  return { backgroundColor: 'rgba(100, 100, 100, 0.3)' }
}

function formatDiff(val: number): string {
  if (Math.abs(val) < 0.005) return '0'
  return (val > 0 ? '+' : '') + val.toFixed(2)
}

function truncLabel(label: string): string {
  if (!label) return ''
  return label.length > 4 ? label.substring(0, 3) + '..' : label
}

// =====================
// Helpers
// =====================
function getCaseName(caseId: string): string {
  return props.designCases.find(dc => dc.id === caseId)?.name || caseId
}

function getCaseColor(caseId: string): string {
  return props.designCases.find(dc => dc.id === caseId)?.color || '#635d73'
}

// =====================
// Lifecycle & Watchers
// =====================
onMounted(() => {
  initializeWeights()
  nextTick(() => {
    renderParallelCoordinates()
  })
})

watch(() => props.designCases, () => {
  initializeWeights()
  nextTick(() => renderParallelCoordinates())
}, { deep: true })

watch(() => props.performances, () => {
  initializeWeights()
  nextTick(() => renderParallelCoordinates())
}, { deep: true })

watch(highlightedCaseId, () => {
  updateLineStyles()
})

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  if (parallelContainer.value) {
    resizeObserver = new ResizeObserver(() => {
      renderParallelCoordinates()
    })
    resizeObserver.observe(parallelContainer.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
})
</script>

<style scoped lang="scss">
@use 'sass:color';
@use '../../style/color' as *;

.design-case-dashboard {
  display: flex;
  flex-direction: column;
  gap: 2vh;
  padding: 1vh;
}

.dashboard-section {
  background: color.adjust($gray, $lightness: 8%);
  border: 1px solid color.adjust($white, $alpha: -0.95);
  border-radius: 0.8vw;
  padding: clamp(1rem, 2vh, 1.5rem);
}

.dashboard-section h3 {
  margin: 0 0 clamp(0.8rem, 1.5vh, 1rem) 0;
  font-size: clamp(0.95rem, 1.3vw, 1.1rem);
  font-weight: 600;
  color: $white;
  padding-bottom: clamp(0.5rem, 1vh, 0.75rem);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.92);
}

// =====================
// Section 1: Summary Table
// =====================
.table-wrapper {
  overflow-x: auto;
}

.summary-table {
  width: 100%;
  border-collapse: collapse;
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
}

.summary-table th,
.summary-table td {
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.5rem, 1vw, 0.75rem);
  border: 1px solid color.adjust($white, $alpha: -0.92);
  color: $white;
  white-space: nowrap;
}

.summary-table th {
  background: color.adjust($gray, $lightness: 3%);
  font-weight: 600;
  font-size: clamp(0.7rem, 0.85vw, 0.8rem);
  position: sticky;
  top: 0;
  z-index: 1;
}

.summary-table th.sortable {
  cursor: pointer;
  user-select: none;
  transition: background 0.2s ease;

  &:hover {
    background: color.adjust($main_1, $alpha: -0.6);
  }
}

.sort-icon {
  font-size: 0.7em;
  margin-left: 0.3vw;
  color: $main_2;
}

.unit {
  font-weight: 400;
  font-size: 0.85em;
  color: color.adjust($white, $alpha: -0.4);
}

.col-color {
  width: 30px;
  text-align: center;
}

.color-swatch {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  display: inline-block;
  border: 1px solid color.adjust($white, $alpha: -0.7);
}

.col-name {
  font-weight: 500;
}

.col-metric {
  text-align: right;
}

.summary-table td.best-value {
  background: color.adjust($sub_4, $alpha: -0.85);
  font-weight: 600;
}

.summary-table tr.highlighted {
  background: color.adjust($main_1, $alpha: -0.65) !important;

  td {
    border-color: color.adjust($main_1, $alpha: -0.4);
  }
}

.summary-table tr.filtered {
  opacity: 0.3;
}

.summary-table tbody tr {
  transition: background 0.15s ease, opacity 0.2s ease;

  &:hover {
    background: color.adjust($main_1, $alpha: -0.75);
  }
}

// =====================
// Section 2: Parallel Coordinates
// =====================
.parallel-svg-container {
  width: 100%;
  height: clamp(280px, 38vh, 420px);
  background: color.adjust($gray, $lightness: 3%);
  border: 1px solid color.adjust($white, $alpha: -0.92);
  border-radius: 0.5vw;
  overflow: hidden;

  :deep(svg) {
    display: block;
    width: 100%;
    height: 100%;

    .brush .selection {
      fill: color.adjust($main_2, $alpha: -0.6);
      stroke: $main_2;
      stroke-width: 1;
    }

    .brush .overlay {
      cursor: crosshair;
    }
  }
}

// =====================
// Section 3: Weighted Scoring
// =====================
.scoring-layout {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 2vw;
  min-height: 0;
}

.sliders-panel {
  display: flex;
  flex-direction: column;
  gap: 0.6vh;
  padding-right: 0.5vw;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 0.8vw;

  label {
    min-width: clamp(60px, 8vw, 100px);
    font-size: clamp(0.72rem, 0.85vw, 0.8rem);
    color: color.adjust($white, $alpha: -0.3);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.weight-slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 5px;
  background: color.adjust($white, $alpha: -0.85);
  border-radius: 3px;
  outline: none;
  cursor: pointer;

  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: $main_2;
    cursor: pointer;
    border: 2px solid $white;
    transition: transform 0.15s ease;
  }

  &::-webkit-slider-thumb:hover {
    transform: scale(1.2);
  }

  &::-moz-range-thumb {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: $main_2;
    cursor: pointer;
    border: 2px solid $white;
  }
}

.weight-value {
  min-width: 2.5em;
  text-align: right;
  font-size: clamp(0.7rem, 0.85vw, 0.8rem);
  font-weight: 600;
  color: $main_2;
  font-variant-numeric: tabular-nums;
}

.ranking-panel {
  display: flex;
  flex-direction: column;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 0.4vh;
}

.rank-bar-row {
  display: flex;
  align-items: center;
  gap: 0.6vw;
  padding: clamp(0.35rem, 0.7vh, 0.5rem) clamp(0.4rem, 0.8vw, 0.6rem);
  border-radius: 0.4vw;
  transition: background 0.2s ease, opacity 0.2s ease, transform 0.3s ease;
  cursor: default;

  &.highlighted {
    background: color.adjust($main_1, $alpha: -0.65);
  }

  &.filtered {
    opacity: 0.3;
  }

  &:hover {
    background: color.adjust($main_1, $alpha: -0.75);
  }
}

.rank-number {
  min-width: 1.8em;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  font-weight: 700;
  color: color.adjust($white, $alpha: -0.3);
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.rank-color-swatch {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  flex-shrink: 0;
  border: 1px solid color.adjust($white, $alpha: -0.7);
}

.rank-name {
  min-width: clamp(60px, 8vw, 120px);
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  font-weight: 500;
  color: $white;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rank-bar-wrapper {
  flex: 1;
  height: clamp(1rem, 1.8vh, 1.4rem);
  background: color.adjust($white, $alpha: -0.92);
  border-radius: 0.3vw;
  overflow: hidden;
}

.rank-bar-fill {
  height: 100%;
  border-radius: 0.3vw;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 2px;
}

.rank-score {
  min-width: 3em;
  text-align: right;
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  font-weight: 600;
  color: $white;
  font-variant-numeric: tabular-nums;
}

.rank-list-move {
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.rank-list-enter-active,
.rank-list-leave-active {
  transition: all 0.3s ease;
}

.rank-list-enter-from,
.rank-list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

// =====================
// Section 4: Matrix Comparison
// =====================
.matrix-controls {
  margin-bottom: 1.5vh;
}

.control-row {
  display: flex;
  align-items: center;
  gap: 1vw;
  flex-wrap: wrap;

  label {
    font-weight: 500;
    color: $white;
    font-size: clamp(0.8rem, 1vw, 0.9rem);
  }
}

.matrix-select {
  padding: clamp(0.4rem, 0.7vh, 0.5rem) clamp(0.6rem, 1vw, 0.8rem);
  background: color.adjust($gray, $lightness: 15%);
  border: 1px solid color.adjust($white, $alpha: -0.85);
  border-radius: 0.4vw;
  color: $white;
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  cursor: pointer;
  min-width: 180px;

  option {
    background: color.adjust($gray, $lightness: 15%);
    color: $white;
  }
}

.load-matrix-btn {
  padding: clamp(0.4rem, 0.7vh, 0.5rem) clamp(1rem, 1.5vw, 1.2rem);
  background: linear-gradient(135deg, $main_1, $main_2);
  color: $white;
  border: none;
  border-radius: 0.4vw;
  font-weight: 600;
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 0.3vh 1vh color.adjust($main_2, $alpha: -0.6);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

// Cell comparison
.cell-comparison {
  margin-bottom: 2vh;
  padding: clamp(0.8rem, 1.5vh, 1rem);
  background: color.adjust($gray, $lightness: 3%);
  border: 1px solid color.adjust($white, $alpha: -0.92);
  border-radius: 0.5vw;

  h4 {
    margin: 0 0 1vh 0;
    font-size: clamp(0.85rem, 1.1vw, 0.95rem);
    font-weight: 600;
    color: $white;
  }
}

.cell-comparison-subtitle {
  font-weight: 400;
  font-size: 0.85em;
  color: color.adjust($white, $alpha: -0.4);
  margin-left: 0.5vw;
}

.cell-bars {
  display: flex;
  flex-direction: column;
  gap: 0.3vh;
}

.cell-bar-row {
  display: flex;
  align-items: center;
  gap: 0.6vw;
  padding: clamp(0.25rem, 0.5vh, 0.35rem) clamp(0.3rem, 0.6vw, 0.4rem);
  border-radius: 0.3vw;
  transition: background 0.15s ease;

  &.highlighted {
    background: color.adjust($main_1, $alpha: -0.65);
  }

  &:hover {
    background: color.adjust($main_1, $alpha: -0.8);
  }
}

.cell-bar-color {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}

.cell-bar-name {
  min-width: clamp(60px, 8vw, 100px);
  font-size: clamp(0.7rem, 0.85vw, 0.8rem);
  color: $white;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-bar-track {
  flex: 1;
  height: clamp(0.8rem, 1.4vh, 1rem);
  background: color.adjust($white, $alpha: -0.92);
  border-radius: 0.2vw;
  position: relative;
  overflow: hidden;
}

.cell-bar-fill {
  position: absolute;
  top: 0;
  height: 100%;
  background: $sub_4;
  border-radius: 0.2vw;
  transition: width 0.3s ease, left 0.3s ease;

  &.negative {
    background: $sub_1;
  }
}

.cell-bar-zero {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 1px;
  background: color.adjust($white, $alpha: -0.5);
}

.cell-bar-value {
  min-width: 4em;
  text-align: right;
  font-size: clamp(0.7rem, 0.85vw, 0.8rem);
  font-weight: 600;
  color: $sub_4;
  font-variant-numeric: tabular-nums;

  &.negative {
    color: $sub_1;
  }
}

// Baseline diff / Individual matrices
.baseline-info {
  margin-bottom: 1vh;
  font-size: clamp(0.8rem, 1vw, 0.9rem);
  color: color.adjust($white, $alpha: -0.3);

  strong {
    color: $white;
  }
}

.diff-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(clamp(220px, 20vw, 300px), 1fr));
  gap: clamp(0.8rem, 1.5vw, 1.2rem);
}

.diff-card {
  background: color.adjust($gray, $lightness: 3%);
  border: 1px solid color.adjust($white, $alpha: -0.92);
  border-radius: 0.5vw;
  overflow: hidden;
  transition: border-color 0.2s ease;

  &.highlighted {
    border-color: color.adjust($main_1, $alpha: -0.3);
  }

  &:hover {
    border-color: color.adjust($main_2, $alpha: -0.5);
  }
}

.diff-card-header {
  display: flex;
  align-items: center;
  gap: 0.5vw;
  padding: clamp(0.4rem, 0.8vh, 0.6rem) clamp(0.5rem, 1vw, 0.75rem);
  background: color.adjust($gray, $lightness: 1%);
  border-bottom: 1px solid color.adjust($white, $alpha: -0.92);
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  font-weight: 600;
  color: $white;
}

.diff-card-color {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}

.diff-matrix-wrapper {
  padding: clamp(0.3rem, 0.6vh, 0.5rem);
  overflow-x: auto;
}

.mini-matrix {
  width: 100%;
  border-collapse: collapse;
  font-size: clamp(0.6rem, 0.75vw, 0.7rem);
  font-variant-numeric: tabular-nums;
}

.mini-matrix th,
.mini-matrix td {
  padding: clamp(0.15rem, 0.3vh, 0.25rem) clamp(0.2rem, 0.4vw, 0.3rem);
  border: 1px solid color.adjust($white, $alpha: -0.92);
  text-align: center;
  color: $white;
  min-width: 32px;
}

.mini-matrix th {
  background: color.adjust($gray, $lightness: 1%);
  font-weight: 500;
  font-size: clamp(0.55rem, 0.7vw, 0.65rem);
}

.mini-matrix td.diagonal {
  background: color.adjust($gray, $lightness: 5%);
  color: color.adjust($white, $alpha: -0.5);
}

.clickable-cell {
  cursor: pointer;
  transition: outline 0.1s ease;

  &:hover {
    outline: 2px solid $main_2;
    outline-offset: -2px;
  }
}

.diff-matrix-loading {
  padding: 2vh;
  text-align: center;
  color: color.adjust($white, $alpha: -0.5);
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
}

.matrix-placeholder {
  padding: 4vh 2vw;
  text-align: center;
  color: color.adjust($white, $alpha: -0.5);
  font-size: clamp(0.85rem, 1vw, 0.95rem);
}

.individual-matrices {
  margin-top: 1vh;
}

// =====================
// Responsive
// =====================
@media (max-width: 900px) {
  .scoring-layout {
    grid-template-columns: 1fr;
  }

  .sliders-panel {
    max-height: none;
  }

  .diff-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .design-case-dashboard {
    gap: 1.5vh;
    padding: 0.5vh;
  }

  .dashboard-section {
    padding: clamp(0.75rem, 1.5vh, 1rem);
  }
}
</style>
