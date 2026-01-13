<template>
  <div class="need-performance-matrix">
    <div class="matrix-toolbar">
      <button class="toolbar-button template-download-button" @click="downloadTemplateFile">
        <svg width="20" height="20" viewBox="0 0 48 48" class="excel-icon">
          <defs>
            <linearGradient id="toolbar-excel-gradient" x1="5.822" y1="11.568" x2="20.178" y2="36.432" gradientUnits="userSpaceOnUse">
              <stop offset="0" stop-color="#18884f"/>
              <stop offset=".5" stop-color="#117e43"/>
              <stop offset="1" stop-color="#0b6631"/>
            </linearGradient>
          </defs>
          <path d="M29 23l-17-3v22.167A1.833 1.833 0 0 0 13.833 44h29.334A1.833 1.833 0 0 0 45 42.167V34z" fill="#185c37"/>
          <path d="M29 4H13.833A1.833 1.833 0 0 0 12 5.833V14l17 10 9 3 7-3V14z" fill="#21a366"/>
          <path fill="#107c41" d="M12 14h17v10H12z"/>
          <path d="M24.167 12H12v25h12.167A1.839 1.839 0 0 0 26 35.167V13.833A1.839 1.839 0 0 0 24.167 12z" opacity=".1"/>
          <path d="M23.167 13H12v25h11.167A1.839 1.839 0 0 0 25 36.167V14.833A1.839 1.839 0 0 0 23.167 13z" opacity=".2"/>
          <path d="M23.167 13H12v23h11.167A1.839 1.839 0 0 0 25 34.167V14.833A1.839 1.839 0 0 0 23.167 13z" opacity=".2"/>
          <path d="M22.167 13H12v23h10.167A1.839 1.839 0 0 0 24 34.167V14.833A1.839 1.839 0 0 0 22.167 13z" opacity=".2"/>
          <rect x="2" y="13" width="22" height="22" rx="1.833" fill="url(#toolbar-excel-gradient)"/>
          <path d="M7.677 29.958l3.856-5.975L8 18.041h2.842l1.928 3.8c.178.361.3.629.366.806h.025q.19-.432.4-.839l2.061-3.765h2.609l-3.623 5.907 3.715 6.008h-2.776l-2.227-4.171a3.5 3.5 0 0 1-.266-.557h-.033a2.638 2.638 0 0 1-.258.54l-2.293 4.188z" fill="#fff"/>
          <path d="M43.167 4H29v10h16V5.833A1.833 1.833 0 0 0 43.167 4z" fill="#33c481"/>
          <path fill="#107c41" d="M29 24h16v10H29z"/>
        </svg>
        <span>Download Utility Function Template File</span>
      </button>
      
      <div class="toolbar-divider"></div>
      
      <button class="toolbar-button matrix-image-button" @click="downloadMatrixAsImageVertical">
        <FontAwesomeIcon :icon="['fas', 'camera']" />
        <span>Download Matrix as Image</span>
      </button>
      
      <button class="toolbar-button matrix-excel-button" @click="downloadMatrixAsExcel">
        <svg width="20" height="20" viewBox="0 0 48 48" class="excel-icon">
          <defs>
            <linearGradient id="matrix-excel-gradient" x1="5.822" y1="11.568" x2="20.178" y2="36.432" gradientUnits="userSpaceOnUse">
              <stop offset="0" stop-color="#18884f"/>
              <stop offset=".5" stop-color="#117e43"/>
              <stop offset="1" stop-color="#0b6631"/>
            </linearGradient>
          </defs>
          <path d="M29 23l-17-3v22.167A1.833 1.833 0 0 0 13.833 44h29.334A1.833 1.833 0 0 0 45 42.167V34z" fill="#185c37"/>
          <path d="M29 4H13.833A1.833 1.833 0 0 0 12 5.833V14l17 10 9 3 7-3V14z" fill="#21a366"/>
          <path fill="#107c41" d="M12 14h17v10H12z"/>
          <path d="M24.167 12H12v25h12.167A1.839 1.839 0 0 0 26 35.167V13.833A1.839 1.839 0 0 0 24.167 12z" opacity=".1"/>
          <path d="M23.167 13H12v25h11.167A1.839 1.839 0 0 0 25 36.167V14.833A1.839 1.839 0 0 0 23.167 13z" opacity=".2"/>
          <path d="M23.167 13H12v23h11.167A1.839 1.839 0 0 0 25 34.167V14.833A1.839 1.839 0 0 0 23.167 13z" opacity=".2"/>
          <path d="M22.167 13H12v23h10.167A1.839 1.839 0 0 0 24 34.167V14.833A1.839 1.839 0 0 0 22.167 13z" opacity=".2"/>
          <rect x="2" y="13" width="22" height="22" rx="1.833" fill="url(#matrix-excel-gradient)"/>
          <path d="M7.677 29.958l3.856-5.975L8 18.041h2.842l1.928 3.8c.178.361.3.629.366.806h.025q.19-.432.4-.839l2.061-3.765h2.609l-3.623 5.907 3.715 6.008h-2.776l-2.227-4.171a3.5 3.5 0 0 1-.266-.557h-.033a2.638 2.638 0 0 1-.258.54l-2.293 4.188z" fill="#fff"/>
          <path d="M43.167 4H29v10h16V5.833A1.833 1.833 0 0 0 43.167 4z" fill="#33c481"/>
          <path fill="#107c41" d="M29 24h16v10H29z"/>
        </svg>
        <span>Download Matrix as Excel</span>
      </button>
    </div>

    
    <div v-if="needs.length > 0 && (stakeholders.length > 0 || performances.length > 0)" class="matrix-container">
      <table class="matrix-table">
        
        <thead>
          
          <tr>
            <th :rowspan="maxPerformanceLevel + 1" class="corner-cell">Needs</th>
            <th :colspan="stakeholders.length" class="group-header stakeholder-group">
              Stakeholders
            </th>
            <th :rowspan="maxPerformanceLevel + 1" class="group-header total-votes-header">
              Total Votes
            </th>
            <th :rowspan="maxPerformanceLevel + 1" class="group-header priority-header">
              Priority
            </th>
            <th :colspan="getAllPerformanceColumns().length" class="group-header performance-group">
              Performances (Hierarchical View)
            </th>
          </tr>
          
          
          <tr v-for="level in maxPerformanceLevel" :key="`level-${level}`">
            
            <template v-if="level === 1">
              <th 
                v-for="stakeholder in stakeholders" 
                :key="stakeholder.id"
                :rowspan="maxPerformanceLevel"
                class="stakeholder-header"
              >
                <div class="stakeholder-header-content">
                  <div class="stakeholder-name-vertical">{{ stakeholder.name }}</div>
                  <div class="stakeholder-votes-horizontal">{{ stakeholder.votes }}</div>
                </div>
              </th>
            </template>
            
            
            <th
              v-for="cell in getMatrixCellsAtLevel(level)"
              :key="cell.performance.id"
              :colspan="cell.colspan"
              :rowspan="cell.rowspan"
              :class="[
                'performance-header', 
                `level-${level}`, 
                `root-${getRootIndexForPerformance(cell.performance.id) % 8}`,
                { 'is-leaf': cell.performance.is_leaf }
              ]"
            >
              <div class="header-content">
                <span>{{ cell.performance.name }}</span>
                <span v-if="cell.performance.unit" class="unit-text">({{ cell.performance.unit }})</span>
              </div>
            </th>
          </tr>
        </thead>

        
        <tbody>
          <tr v-for="need in needs" :key="need.id">
            
            <td class="need-header">
              <div class="need-info">
                {{ need.name }}
                <span v-if="need.category" class="category-tag">
                  {{ need.category }}
                </span>
              </div>
            </td>

            
            <td
              v-for="stakeholder in stakeholders"
              :key="`sh-${stakeholder.id}`"
              class="matrix-cell stakeholder-cell"
              :class="{ active: hasStakeholderRelation(stakeholder.id, need.id) }"
              @click="toggleStakeholderRelation(stakeholder.id, need.id)"
            >
              <div class="cell-content">
                <template v-if="hasStakeholderRelation(stakeholder.id, need.id)">
                  {{ getStakeholderVotesForNeed(stakeholder.id, need.id).toFixed(1) }}
                </template>
              </div>
            </td>

            
            <td class="matrix-cell total-votes-cell">
              <div class="cell-content total-votes-value">
                {{ getRawTotalVotesForNeed(need.id).toFixed(1) }}
              </div>
            </td>

            
            <td class="matrix-cell priority-cell">
              <input
                type="number"
                class="priority-input"
                min="0"
                max="1"
                step="0.01"
                :value="need.priority || 1.0"
                @input="updateNeedPriority(need.id, $event)"
                placeholder="1.0"
              />
            </td>

            
            <td
              v-for="perf in getAllPerformanceColumns()"
              :key="`perf-${perf.id}`"
              class="matrix-cell performance-cell"
              :class="[
                getPerformanceRelationClass(need.id, perf.id),
                { 
                  'non-leaf': !perf.is_leaf,
                  'unchecked': isUncheckedCell(need.id, perf.id)
                }
              ]"
              @click="perf.is_leaf ? cyclePerformanceRelation(need.id, perf.id) : null"
            >
              <div class="cell-content">
                <template v-if="perf.is_leaf">
                  
                  <button
                    v-if="getUtilityButtonType(need.id, perf.id) !== 'none'"
                    class="utility-button"
                    :class="`utility-button-${getUtilityButtonType(need.id, perf.id)}`"
                    @click="openUtilityModal(need.id, perf.id, $event)"
                    :title="getUtilityButtonType(need.id, perf.id) === 'warning' ? 'Utility function needs review' : 'Set utility function'"
                  >
                    <span v-if="getUtilityButtonType(need.id, perf.id) === 'add'">+</span>
                    <span v-else-if="getUtilityButtonType(need.id, perf.id) === 'check'">✓</span>
                    <span v-else-if="getUtilityButtonType(need.id, perf.id) === 'warning'">!</span>
                  </button>
                  
                  <span class="arrow-symbol">{{ getPerformanceRelationSymbol(need.id, perf.id) }}</span>
                  <span v-if="getPerformanceRelation(need.id, perf.id)" class="performance-votes">
                    {{ getPerformanceVotesForNeed(need.id, perf.id).toFixed(1) }}
                  </span>
                </template>
                <template v-else>
                  <span class="non-leaf-indicator">-</span>
                </template>
              </div>
            </td>
          </tr>

          
          <tr class="summary-row">
            <td :colspan="stakeholders.length + 2" class="summary-empty"></td>
            <td class="summary-label-cell">↑Votes</td>
            <td
              v-for="perf in getAllPerformanceColumns()"
              :key="`up-${perf.id}`"
              class="summary-cell"
            >
              <span v-if="perf.is_leaf" class="summary-value">{{ getUpVotesForPerformance(perf.id).toFixed(1) }}</span>
            </td>
          </tr>

          
          <tr class="summary-row">
            <td :colspan="stakeholders.length + 2" class="summary-empty"></td>
            <td class="summary-label-cell">↓Votes</td>
            <td
              v-for="perf in getAllPerformanceColumns()"
              :key="`down-${perf.id}`"
              class="summary-cell"
            >
              <span v-if="perf.is_leaf" class="summary-value">{{ getDownVotesForPerformance(perf.id).toFixed(1) }}</span>
            </td>
          </tr>


          <!-- Valid Votes行（一時的にコメントアウト）
          <tr class="summary-row effective-votes-row">
            <td :colspan="stakeholders.length + 2" class="summary-empty effective-votes-empty"></td>
            <td class="summary-label-cell effective-votes-label">Valid Votes</td>
            <td
              v-for="perf in getAllPerformanceColumns()"
              :key="`effective-${perf.id}`"
              class="summary-cell effective-votes-cell"
            >
              <span v-if="perf.is_leaf" class="summary-value">{{ getNormalizedEffectiveVotesForPerformance(perf.id).toFixed(3) }}</span>
            </td>
          </tr>
          -->

          
          <tr class="summary-row root-summary-row">
            <td :colspan="stakeholders.length + 2" class="summary-empty root-summary-empty"></td>
            <td class="summary-label-cell root-summary-label">V</td>
            <td
              v-for="group in rootGroups"
              :key="`root-${group.rootIndex}`"
              :colspan="group.colspan"
              :class="['summary-cell', 'root-summary-cell', `root-cell-${group.rootIndex % 8}`]"
            >
              <span class="root-value">{{ getEffectiveVotesForRoot(group.rootIndex).toFixed(1) }}</span>
            </td>
          </tr>

          
          <tr class="summary-row p-value-row">
            <td :colspan="stakeholders.length + 2" class="summary-empty p-value-empty"></td>
            <td class="summary-label-cell p-value-label">p= Σv_i / V</td>
            <td
              v-for="perf in getAllPerformanceColumns()"
              :key="`p-${perf.id}`"
              class="summary-cell p-value-cell"
            >
              <span v-if="perf.is_leaf" class="summary-value">{{ getPValueForPerformance(perf.id).toFixed(3) }}</span>
            </td>
          </tr>

          
          <tr class="summary-row p-squared-row">
            <td :colspan="stakeholders.length + 2" class="summary-empty p-squared-empty"></td>
            <td class="summary-label-cell p-squared-label">p²</td>
            <td
              v-for="perf in getAllPerformanceColumns()"
              :key="`p2-${perf.id}`"
              class="summary-cell p-squared-cell"
              :style="{ backgroundColor: perf.is_leaf ? getColorScaleGreenYellowRed(getPSquaredForPerformance(perf.id), pSquaredMin, pSquaredMax) : '' }"
            >
              <span v-if="perf.is_leaf" class="summary-value">{{ getPSquaredForPerformance(perf.id).toFixed(4) }}</span>
            </td>
          </tr>

          
          <tr class="summary-row hhi-row">
            <td :colspan="stakeholders.length + 2" class="summary-empty hhi-empty"></td>
            <td class="summary-label-cell hhi-label">HHI = Σp²</td>
            <td
              v-for="group in rootGroups"
              :key="`hhi-${group.rootIndex}`"
              :colspan="group.colspan"
              class="summary-cell hhi-cell"
              :style="{ backgroundColor: getColorScaleGreenYellowRed(getHHIForRoot(group.rootIndex), hhiMin, hhiMax) }"
            >
              <span class="summary-value hhi-value">{{ getHHIForRoot(group.rootIndex).toFixed(4) }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    
    <DecompositionAnalysis
      :analysis="insufficientDecompositionAnalysis"
      :needsCount="needs.length"
      :hasStakeholdersOrPerformances="stakeholders.length > 0 || performances.length > 0"
      @navigate-to-performance="navigateToPerformanceManagement"
    />

    
    <div v-if="showUtilityModal && currentUtilityEdit" class="modal-overlay" @click="closeUtilityModal">
      <div class="modal-content utility-modal" @click.stop>
        <h3>Utility Function Settings</h3>
        
        <div class="modal-info">
          <div class="info-row">
            <strong>Performance:</strong>
            <span>{{ performances.find(p => p.id === currentUtilityEdit!.performanceId)?.name }}</span>
          </div>
          <div class="info-row">
            <strong>Needs:</strong>
            <span>{{ needs.find(n => n.id === currentUtilityEdit!.needId)?.name }}</span>
          </div>
          <div class="info-row">
            <strong>Direction:</strong>
            <span class="direction-badge">
              {{ getPerformanceRelationSymbol(currentUtilityEdit!.needId, currentUtilityEdit!.performanceId) }}
              {{ getPerformanceRelation(currentUtilityEdit!.needId, currentUtilityEdit!.performanceId)?.direction === 'up' ? 'Increase' : 'Decrease' }}
            </span>
          </div>
        </div>

        <div class="graph-section">
          <div class="graph-container">
            
            <div class="graph-controls">
              
              <button 
                class="graph-control-button import-button" 
                @click.stop="handleImportExcel"
                title="Import utility function from Excel"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                  <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/>
                </svg>
              </button>
              
              <button 
                v-if="hasUtilityFunction()"
                class="graph-control-button camera-button" 
                @click.stop="handleDownloadGraph"
                title="Download graph as image"
              >
                <FontAwesomeIcon :icon="['fas', 'camera']" />
              </button>
              
              <button 
                v-if="hasUtilityFunction()"
                class="graph-control-button excel-button" 
                @click.stop="handleDownloadExcel"
                title="Download utility function as Excel"
              >
                <svg width="16" height="16" viewBox="0 0 48 48">
                  <defs>
                    <linearGradient id="excel-gradient" x1="5.822" y1="11.568" x2="20.178" y2="36.432" gradientUnits="userSpaceOnUse">
                      <stop offset="0" stop-color="#18884f"/>
                      <stop offset=".5" stop-color="#117e43"/>
                      <stop offset="1" stop-color="#0b6631"/>
                    </linearGradient>
                  </defs>
                  <path d="M29 23l-17-3v22.167A1.833 1.833 0 0 0 13.833 44h29.334A1.833 1.833 0 0 0 45 42.167V34z" fill="#185c37"/>
                  <path d="M29 4H13.833A1.833 1.833 0 0 0 12 5.833V14l17 10 9 3 7-3V14z" fill="#21a366"/>
                  <path fill="#107c41" d="M12 14h17v10H12z"/>
                  <path d="M24.167 12H12v25h12.167A1.839 1.839 0 0 0 26 35.167V13.833A1.839 1.839 0 0 0 24.167 12z" opacity=".1"/>
                  <path d="M23.167 13H12v25h11.167A1.839 1.839 0 0 0 25 36.167V14.833A1.839 1.839 0 0 0 23.167 13z" opacity=".2"/>
                  <path d="M23.167 13H12v23h11.167A1.839 1.839 0 0 0 25 34.167V14.833A1.839 1.839 0 0 0 23.167 13z" opacity=".2"/>
                  <path d="M22.167 13H12v23h10.167A1.839 1.839 0 0 0 24 34.167V14.833A1.839 1.839 0 0 0 22.167 13z" opacity=".2"/>
                  <rect x="2" y="13" width="22" height="22" rx="1.833" fill="url(#excel-gradient)"/>
                  <path d="M7.677 29.958l3.856-5.975L8 18.041h2.842l1.928 3.8c.178.361.3.629.366.806h.025q.19-.432.4-.839l2.061-3.765h2.609l-3.623 5.907 3.715 6.008h-2.776l-2.227-4.171a3.5 3.5 0 0 1-.266-.557h-.033a2.638 2.638 0 0 1-.258.54l-2.293 4.188z" fill="#fff"/>
                  <path d="M43.167 4H29v10h16V5.833A1.833 1.833 0 0 0 43.167 4z" fill="#33c481"/>
                  <path fill="#107c41" d="M29 24h16v10H29z"/>
                </svg>
              </button>
              
              <button 
                v-if="hasUtilityFunction()"
                class="graph-control-button copy-button" 
                @click.stop="handleCopyUtilityFunction"
                title="Copy utility function"
              >
                <FontAwesomeIcon :icon="['fas', 'copy']" />
              </button>
              
              <button 
                v-if="canPasteUtilityFunction()"
                class="graph-control-button paste-button" 
                @click.stop="handlePasteUtilityFunction"
                title="Paste utility function"
              >
                <FontAwesomeIcon :icon="['fas', 'paste']" />
              </button>
              <button 
                class="graph-control-button info-button" 
                @click.stop="toggleInfoPopup"
                title="How to use"
              >
                <FontAwesomeIcon :icon="['fas', 'info-circle']" />
              </button>
              <button 
                class="graph-control-button settings-button" 
                @click.stop="toggleSettingsPopup"
                title="Settings"
              >
                <FontAwesomeIcon :icon="['fas', 'gear']" />
              </button>
              
              
              <div v-if="showInfoPopup" class="graph-popup info-popup" @click.stop>
                <div class="popup-header">
                  <h4>How to Use the Graph</h4>
                  <button class="popup-close" @click="showInfoPopup = false">×</button>
                </div>
                <div class="popup-content">
                  <p class="info-section-title">[Continuous Function]</p>
                  <ul class="info-list">
                    <li><strong>Plot points:</strong> Click inside the graph</li>
                    <li><strong>Delete points:</strong> Click on plotted points</li>
                    <li><strong>Line display:</strong> Automatically connects with 2+ points</li>
                    <li><strong>Check coordinates:</strong> Hover over points</li>
                    <li><strong>Axis range:</strong> Adjustable with slider below</li>
                  </ul>
                  <p class="info-section-title">[Discrete Function]</p>
                  <ul class="info-list">
                    <li><strong>Plot points:</strong> Click in graph to update nearest point's utility value</li>
                    <li><strong>Delete points:</strong> Click green points (or delete row in matrix)</li>
                    <li><strong>Check coordinates:</strong> Hover over points</li>
                  </ul>
                  <p class="info-section-title">[Copy & Paste]</p>
                  <ul class="info-list">
                    <li><strong>Copy:</strong> <FontAwesomeIcon :icon="['fas', 'copy']" /> button appears when utility function is registered</li>
                    <li><strong>Paste:</strong> Only available for different Needs with the same Performance</li>
                  </ul>
                </div>
              </div>
              
              
              <div v-if="showSettingsPopup" class="graph-popup settings-popup" @click.stop>
                <div class="popup-header">
                  <h4>Line Interpolation Settings</h4>
                  <button class="popup-close" @click="showSettingsPopup = false">×</button>
                </div>
                <div class="popup-content">
                  <div class="setting-item">
                    <label class="setting-label">Interpolation Method (Continuous Function Only):</label>
                    <select v-model="interpolationType" class="setting-select" :disabled="currentUtilityEdit?.type === 'discrete'">
                      <option value="linear">Linear Interpolation</option>
                      <option value="step">Step Interpolation</option>
                      <option value="smooth">Smooth Interpolation</option>
                    </select>
                  </div>
                  <div class="setting-description">
                    <template v-if="currentUtilityEdit?.type === 'discrete'">
                      Lines are not displayed for discrete functions. Each discrete value is shown as an independent point.
                    </template>
                    <template v-else-if="interpolationType === 'linear'">
                      Connects points with straight lines (default)
                    </template>
                    <template v-else-if="interpolationType === 'step'">
                      Interpolates with step-like transitions (stepwise changes)
                    </template>
                    <template v-else-if="interpolationType === 'smooth'">
                      Interpolates smoothly with curves
                    </template>
                  </div>
                </div>
              </div>
            </div>
            
            <svg class="utility-graph" viewBox="0 0 420 330" preserveAspectRatio="xMidYMid meet" @click="handleGraphClick">
              
              <rect x="50" y="20" width="330" height="260" fill="#f8f9fa" stroke="#dee2e6" stroke-width="1"/>
              
              
              <line v-for="i in 10" :key="`v-${i}`" 
                :x1="50 + i * 33" :y1="20" 
                :x2="50 + i * 33" :y2="280" 
                stroke="#e9ecef" stroke-width="1"/>
              
              
              <line v-for="i in 10" :key="`h-${i}`" 
                :x1="50" :y1="20 + i * 26" 
                :x2="380" :y2="20 + i * 26" 
                stroke="#e9ecef" stroke-width="1"/>
              
              
              <line x1="50" :y1="20 + 260 * 0.5" x2="380" :y2="20 + 260 * 0.5" 
                stroke="#fbbf24" stroke-width="2" stroke-dasharray="5,5" opacity="0.7"/>
              
              
              <line x1="50" :y1="20 + 260 * 0.2" x2="380" :y2="20 + 260 * 0.2" 
                stroke="#ef4444" stroke-width="2" stroke-dasharray="5,5" opacity="0.7"/>
              
              
              <line x1="50" y1="20" x2="50" y2="280" stroke="#495057" stroke-width="2"/>
              
              
              <line x1="50" y1="280" x2="380" y2="280" stroke="#495057" stroke-width="2"/>
              
              
              <g v-if="currentUtilityEdit?.type === 'continuous'" v-for="(point, index) in utilityPoints" :key="`point-${index}`">
                <circle 
                  :cx="point.x" 
                  :cy="point.y" 
                  r="5" 
                  fill="#3b82f6" 
                  stroke="#1e40af" 
                  stroke-width="2"
                  class="utility-point"
                  @click.stop="removePoint(index)"
                  @mouseenter="showTooltip(point, $event)"
                  @mouseleave="hideTooltip"
                  style="cursor: pointer;"
                />
              </g>
              
              
              <g v-if="currentUtilityEdit?.type === 'discrete'" v-for="(point, index) in discreteGraphPoints" :key="`discrete-${index}`">
                <circle 
                  :cx="point.x" 
                  :cy="point.y" 
                  r="6" 
                  fill="#10b981" 
                  stroke="#059669" 
                  stroke-width="2"
                  class="utility-point discrete-point"
                  @click.stop="removeDiscreteRow(index)"
                  @mouseenter="showDiscreteTooltip(point, index, $event)"
                  @mouseleave="hideTooltip"
                  style="cursor: pointer;"
                />
              </g>
              
              
              <g v-if="tooltip.visible" class="custom-tooltip">
                <rect 
                  :x="tooltip.x - 60" 
                  :y="tooltip.y - 28" 
                  width="120" 
                  height="24" 
                  rx="4"
                  fill="#212529" 
                  opacity="0.9"
                />
                <text 
                  :x="tooltip.x" 
                  :y="tooltip.y - 12" 
                  font-size="11" 
                  fill="white" 
                  text-anchor="middle"
                  font-weight="500"
                >
                  {{ tooltip.content }}
                </text>
              </g>
              
              
              <polyline 
                v-if="currentUtilityEdit?.type === 'continuous' && utilityPoints.length > 1 && interpolationType !== 'smooth'"
                :points="getPolylinePoints()"
                fill="none"
                stroke="#3b82f6"
                stroke-width="2"
                opacity="0.6"
                :key="`polyline-${utilityPoints.length}-${interpolationType}`"
              />
              
              
              <path
                v-if="currentUtilityEdit?.type === 'continuous' && utilityPoints.length > 1 && interpolationType === 'smooth'"
                :d="getSmoothPath()"
                fill="none"
                stroke="#3b82f6"
                stroke-width="2"
                opacity="0.6"
                :key="`path-${utilityPoints.length}-${interpolationType}`"
              />
              
              
              <text x="25" y="25" font-size="12" fill="#f3f3f3" font-weight="600">1.0</text>
              <text x="25" y="153" font-size="12" fill="#f3f3f3" font-weight="600">0.5</text>
              <text x="25" y="283" font-size="12" fill="#f3f3f3" font-weight="600">0.0</text>
              
              
              <text x="15" y="150" font-size="14" fill="#f3f3f3" font-weight="600" 
                transform="rotate(-90, 15, 150)">Utility Value</text>
              
              
              <template v-if="currentUtilityEdit?.type === 'continuous'">
                <text x="50" y="295" font-size="11" fill="#f3f3f3" text-anchor="middle">{{ axisRange.min }}</text>
                <text x="215" y="295" font-size="11" fill="#f3f3f3" text-anchor="middle">{{ ((axisRange.min + axisRange.max) / 2).toFixed(2) }}</text>
                <text x="380" y="295" font-size="11" fill="#f3f3f3" text-anchor="middle">{{ axisRange.max }}</text>
              </template>
              
              
              <template v-if="currentUtilityEdit?.type === 'discrete'">
                <g v-for="(row, index) in discreteRows" :key="`label-${index}`">
                  <text 
                    :x="getDiscreteXPosition(index)" 
                    y="295" 
                    font-size="10" 
                    fill="#f3f3f3" 
                    text-anchor="middle"
                  >
                    {{ row.label || `#${index + 1}` }}
                  </text>
                </g>
              </template>
              
              
              <text x="215" y="310" font-size="14" fill="#f3f3f3" font-weight="600" 
                text-anchor="middle">
                {{ getCurrentPerformanceUnit() ? `${performances.find(p => p.id === currentUtilityEdit!.performanceId)?.name} (${getCurrentPerformanceUnit()})` : `${performances.find(p => p.id === currentUtilityEdit!.performanceId)?.name}` }}
              </text>
              
              
              <text x="385" :y="20 + 260 * 0.5 + 5" font-size="11" fill="#f59e0b" font-weight="600">0.5</text>
              <text x="385" :y="20 + 260 * 0.2 + 5" font-size="11" fill="#dc2626" font-weight="600">0.8</text>
            </svg>
          </div>
          
          
          <div class="type-switcher">
            <span class="type-label">Type:</span>
            <button 
              class="type-button" 
              :class="{ active: currentUtilityEdit?.type === 'continuous' }"
              @click="switchToType('continuous')"
            >
              <span class="type-icon">{{ currentUtilityEdit?.type === 'continuous' ? '●' : '○' }}</span>
              Continuous
            </button>
            <button 
              class="type-button" 
              :class="{ active: currentUtilityEdit?.type === 'discrete' }"
              @click="switchToType('discrete')"
            >
              <span class="type-icon">{{ currentUtilityEdit?.type === 'discrete' ? '●' : '○' }}</span>
              Discrete
            </button>
          </div>
          
          
          <div v-if="currentUtilityEdit?.type === 'continuous'" class="axis-range-control">
            <div class="range-header">
              <span class="range-label">X-Axis Range:</span>
            </div>
            
            <div class="range-single-row">
              <input 
                type="number" 
                v-model.number="axisRange.min" 
                @input="updateRangeFromInput"
                step="any"
                class="range-input"
                placeholder="Min"
              />
              
              <div ref="rangeSliderElement" class="nouislider-container"></div>
              
              <input 
                type="number" 
                v-model.number="axisRange.max" 
                @input="updateRangeFromInput"
                step="any"
                class="range-input"
                placeholder="Max"
              />
            </div>
          </div>
          
          
          <div v-if="currentUtilityEdit?.type === 'discrete'" class="discrete-matrix-control">
            <div class="matrix-header">
              <span class="matrix-label">Discrete Value Matrix:</span>
              <button class="add-row-button" @click="addDiscreteRow">
                + Add Row
              </button>
            </div>
            
            <div class="discrete-matrix">
              <table class="discrete-table">
                <thead>
                  <tr>
                    <th class="label-column">Performance Value Label</th>
                    <th class="value-column">Utility Value (0-1)</th>
                    <th class="action-column"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in discreteRows" :key="index" class="discrete-row">
                    <td class="label-cell">
                      <input 
                        type="text" 
                        v-model="row.label"
                        class="discrete-input label-input"
                        placeholder="e.g. Small"
                      />
                    </td>
                    <td class="value-cell">
                      <input 
                        type="number" 
                        v-model.number="row.value"
                        class="discrete-input value-input"
                        placeholder="0.0 - 1.0"
                        min="0"
                        max="1"
                        step="0.01"
                      />
                    </td>
                    <td class="action-cell">
                      <button 
                        class="remove-row-button"
                        @click="removeDiscreteRow(index)"
                        :disabled="discreteRows.length <= 1"
                      >
                        ✕
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <div class="matrix-hint">
              You can also set utility values by plotting points on the graph above
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button 
            v-if="getUtilityButtonType(currentUtilityEdit!.needId, currentUtilityEdit!.performanceId) === 'check' || getUtilityButtonType(currentUtilityEdit!.needId, currentUtilityEdit!.performanceId) === 'warning'"
            class="danger" 
            @click="resetUtilityFunction"
          >
            Reset
          </button>
          <div class="spacer"></div>
          <button class="secondary" @click="closeUtilityModal">
            Exit Without Saving
          </button>
          <button class="primary" @click="saveUtilityFunction">
            Save
          </button>
        </div>
      </div>
    </div>

    
    <div v-else-if="!(needs.length > 0 && (stakeholders.length > 0 || performances.length > 0))" class="empty-matrix">
      <p>Please register Stakeholders, Needs, and Performance</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, nextTick, watch } from 'vue'
import { useProjectStore } from '../../stores/projectStore'
import { storeToRefs } from 'pinia'
import type { Performance } from '../../types/project'
import noUiSlider from 'nouislider'
import 'nouislider/dist/nouislider.css'
import type { target as noUiSliderTarget } from 'nouislider'
import * as XLSX from 'xlsx'
import DecompositionAnalysis from './DecompositionAnalysis.vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

const emit = defineEmits<{
  navigateToPerformance: []
}>()

interface UtilityFunction {
  need_id: string
  performance_id: string
  direction: 'up' | 'down'
  type: 'continuous' | 'discrete'
  axisMin?: number 
  axisMax?: number 
  points?: UtilityPoint[] 
  discreteRows?: DiscreteRow[]
  saved: boolean 
  warning: boolean 
  archived: boolean
}

const projectStore = useProjectStore()
const {
  currentProject,
  stakeholders,
  needs,
  performances,
  stakeholderNeedRelations,
  needPerformanceRelations
} = storeToRefs(projectStore)

const utilityFunctions = ref<UtilityFunction[]>([])

const showUtilityModal = ref(false)
const currentUtilityEdit = ref<{
  needId: string
  performanceId: string
  type: 'continuous' | 'discrete'
} | null>(null)

const axisRange = ref({
  min: 0,
  max: 100
})

const rangeSliderElement = ref<HTMLElement | null>(null)
let rangeSliderInstance: any = null

interface UtilityPoint {
  x: number 
  y: number 
  valueX: number 
  valueY: number 
}

const utilityPoints = ref<UtilityPoint[]>([])

interface DiscreteRow {
  label: string 
  value: number 
}

const discreteRows = ref<DiscreteRow[]>([
  { label: '', value: 0 }
])

function addDiscreteRow() {
  discreteRows.value.push({ label: '', value: 0 })
}

function removeDiscreteRow(index: number) {
  if (discreteRows.value.length > 1) {
    discreteRows.value.splice(index, 1)
  }
}

const showInfoPopup = ref(false)
const showSettingsPopup = ref(false)

const interpolationType = ref<'linear' | 'step' | 'smooth'>('linear')

const copiedUtilityFunction = ref<{
  performanceId: string
  type: 'continuous' | 'discrete'
  points: Array<{ x: number; y: number; valueX: number; valueY: number }>
  discreteMapping: Array<{ label: string; value: number }>
  axisRange: { min: number; max: number }
  interpolationType: 'linear' | 'step' | 'smooth'
} | null>(null)

const tooltip = ref<{
  visible: boolean
  x: number
  y: number
  content: string
}>({
  visible: false,
  x: 0,
  y: 0,
  content: ''
})

function toggleInfoPopup() {
  showInfoPopup.value = !showInfoPopup.value
  if (showInfoPopup.value) {
    showSettingsPopup.value = false
  }
}

function toggleSettingsPopup() {
  showSettingsPopup.value = !showSettingsPopup.value
  if (showSettingsPopup.value) {
    showInfoPopup.value = false
  }
}

function handleCopyUtilityFunction() {
  if (!currentUtilityEdit.value) return
  
  copiedUtilityFunction.value = {
    performanceId: currentUtilityEdit.value.performanceId,
    type: currentUtilityEdit.value.type,
    points: [...utilityPoints.value],
    discreteMapping: discreteRows.value.map(row => ({ ...row })),
    axisRange: { ...axisRange.value },
    interpolationType: interpolationType.value
  }
  
}

function handleDownloadGraph() {
  if (!currentUtilityEdit.value) return
  
  const svgElement = document.querySelector('.utility-graph') as SVGElement
  if (!svgElement) return
  
  const svgClone = svgElement.cloneNode(true) as SVGElement
  
  // Change all text elements to black color for better visibility on white background
  const textElements = svgClone.querySelectorAll('text')
  textElements.forEach(text => {
    text.setAttribute('fill', '#000000')
  })
  
  // Change grid lines to darker color for better visibility
  const lines = svgClone.querySelectorAll('line')
  lines.forEach(line => {
    const stroke = line.getAttribute('stroke')
    if (stroke === '#e9ecef') {
      line.setAttribute('stroke', '#dee2e6')
    } else if (stroke === '#495057') {
      line.setAttribute('stroke', '#000000')
    }
  })
  
  // Change background to white
  const bgRect = svgClone.querySelector('rect[fill="#f8f9fa"]')
  if (bgRect) {
    bgRect.setAttribute('fill', '#ffffff')
  }
  
  const svgData = new XMLSerializer().serializeToString(svgClone)
  const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })
  
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  const img = new Image()
  const url = URL.createObjectURL(svgBlob)
  
  img.onload = () => {
    canvas.width = 1260
    canvas.height = 990
    
    ctx.fillStyle = 'white'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
    
    canvas.toBlob((blob) => {
      if (!blob) return
      
      const performance = performances.value.find(p => p.id === currentUtilityEdit.value!.performanceId)
      const need = needs.value.find(n => n.id === currentUtilityEdit.value!.needId)
      const filename = `utility_function_${performance?.name || 'performance'}_${need?.name || 'need'}.png`
      
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = filename
      link.click()
      
      URL.revokeObjectURL(url)
      URL.revokeObjectURL(link.href)
    }, 'image/png')
  }
  
  img.src = url
}

function handleDownloadExcel() {
  if (!currentUtilityEdit.value) return
  
  const performance = performances.value.find(p => p.id === currentUtilityEdit.value!.performanceId)
  const need = needs.value.find(n => n.id === currentUtilityEdit.value!.needId)
  const relation = getPerformanceRelation(currentUtilityEdit.value.needId, currentUtilityEdit.value.performanceId)
  
  const wb = XLSX.utils.book_new()
  
  if (currentUtilityEdit.value.type === 'continuous') {
    const dataRows: (string | number)[][] = [
      ['Continuous Function Data'],
      [''],
      ['Interpolation Method', interpolationType.value === 'linear' ? 'Linear' : interpolationType.value === 'step' ? 'Step' : 'Smooth', 'Please enter either "Linear", "Step", or "Smooth"'],
      ['Axis Range (Min)', axisRange.value.min, ''],
      ['Axis Range (Max)', axisRange.value.max, ''],
      [''],
      ['Performance Value', 'Utility Value']
    ]
    
    const sortedPoints = [...utilityPoints.value].sort((a, b) => a.valueX - b.valueX)
    
    sortedPoints.forEach(point => {
      dataRows.push([point.valueX, point.valueY])
    })
    
    const ws_data = XLSX.utils.aoa_to_sheet(dataRows)
    
    ws_data['!cols'] = [
      { wch: 20 },
      { wch: 15 },
      { wch: 40 }
    ]
    
    XLSX.utils.book_append_sheet(wb, ws_data, 'Continuous Function Data')
  } else {
    const dataRows: (string | number)[][] = [
      ['Discrete Function Data'],
      [''],
      ['Label', 'Utility Value']
    ]
    
    discreteRows.value.forEach(row => {
      if (row.label !== '' || row.value !== 0) {
        dataRows.push([row.label, row.value])
      }
    })
    
    const ws_data = XLSX.utils.aoa_to_sheet(dataRows)
    
    ws_data['!cols'] = [
      { wch: 20 },
      { wch: 15 }
    ]
    
    XLSX.utils.book_append_sheet(wb, ws_data, 'Discrete Function Data')
  }
  
  const filename = `utility_function_${performance?.name || 'performance'}_${need?.name || 'need'}.xlsx`
  XLSX.writeFile(wb, filename)
}

function handleImportExcel() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.xlsx,.xls'
  
  input.onchange = (e: Event) => {
    const target = e.target as HTMLInputElement
    const file = target.files?.[0]
    if (!file) return
    
    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        const data = new Uint8Array(event.target?.result as ArrayBuffer)
        const workbook = XLSX.read(data, { type: 'array' })
        
        let functionType: 'continuous' | 'discrete' | null = null
        
        if (workbook.Sheets['Continuous Function Data']) {
          functionType = 'continuous'
        } else if (workbook.Sheets['Discrete Function Data']) {
          functionType = 'discrete'
        } else {
          alert('Error: "Continuous Function Data" or "Discrete Function Data" sheet not found')
          return
        }
        
        if (functionType === 'continuous') {
          const dataSheet = workbook.Sheets['Continuous Function Data']
          if (!dataSheet) {
            alert('Error: "Continuous Function Data" sheet not found')
            return
          }
          
          const dataJson = XLSX.utils.sheet_to_json(dataSheet, { header: 1 }) as any[][]
          
          const interpolationValue = dataJson[2]?.[1]
          
          let newInterpolationType: 'linear' | 'step' | 'smooth' = 'linear'
          if (typeof interpolationValue === 'string') {
            const normalizedValue = interpolationValue.trim()
            if (normalizedValue === 'Linear' || normalizedValue === 'linear') {
              newInterpolationType = 'linear'
            } else if (normalizedValue === 'Step' || normalizedValue === 'step') {
              newInterpolationType = 'step'
            } else if (normalizedValue === 'Smooth' || normalizedValue === 'smooth') {
              newInterpolationType = 'smooth'
            }
          }
          const minValue = Number(dataJson[3]?.[1])
          const maxValue = Number(dataJson[4]?.[1])
          
          const points: Array<{ x: number; y: number; valueX: number; valueY: number }> = []
          for (let i = 7; i < dataJson.length; i++) {
            const row = dataJson[i]
            if (row && row[0] !== undefined && row[1] !== undefined) {
              const valueX = Number(row[0])
              const valueY = Number(row[1])
              
              if (!isNaN(valueX) && !isNaN(valueY)) {
                const x = 50 + ((valueX - minValue) / (maxValue - minValue)) * 330
                const y = 20 + (1 - valueY) * 260
                
                points.push({ x, y, valueX, valueY })
              }
            }
          }
          
          currentUtilityEdit.value!.type = 'continuous'
          axisRange.value = { min: minValue, max: maxValue }
          interpolationType.value = newInterpolationType
          utilityPoints.value = points
          nextTick(() => {
            initRangeSlider()
            if (utilityPoints.value.length > 0) {
              const temp = [...utilityPoints.value]
              utilityPoints.value = temp
            }
          })
          
          alert(`Continuous function data imported (Interpolation method: ${newInterpolationType === 'linear' ? 'Linear' : newInterpolationType === 'step' ? 'Step' : 'Smooth'})`)
        } else {
          const dataSheet = workbook.Sheets['Discrete Function Data']
          if (!dataSheet) {
            alert('Error: "Discrete Function Data" sheet not found')
            return
          }
          
          const dataJson = XLSX.utils.sheet_to_json(dataSheet, { header: 1 }) as any[][]
          
          const rows: Array<{ label: string; value: number }> = []
          for (let i = 3; i < dataJson.length; i++) {
            const row = dataJson[i]
            if (row && row[0] !== undefined && row[1] !== undefined) {
              const value = Number(row[1])
              if (!isNaN(value)) {
                rows.push({
                  label: String(row[0]),
                  value: value
                })
              }
            }
          }
          
          currentUtilityEdit.value!.type = 'discrete'
          discreteRows.value = rows.length > 0 ? rows : [{ label: '', value: 0 }]
          
          alert('Discrete function data imported')
        }
        
      } catch (error) {
        console.error('Excel loading error:', error)
        alert('Error: Failed to load Excel file')
      }
    }
    
    reader.readAsArrayBuffer(file)
  }
  
  input.click()
}

function downloadTemplateFile() {
  // Works in both Vite dev and production environments
  const link = document.createElement('a')
  link.href = '/templates/utility_function_template.xlsx'
  link.download = 'utility_function_template.xlsx'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

async function downloadMatrixAsImageVertical() {
  try {
    const button = document.querySelector('.matrix-image-button span')
    if (button) {
      button.textContent = 'Generating image...'
    }
    
    let targetElement: HTMLElement | null = null
    
    const matrixTable = document.querySelector('.matrix-table') as HTMLElement
    if (matrixTable && matrixTable.offsetWidth > 0) {
      targetElement = matrixTable
    }
    
    if (!targetElement) {
      const matrixContainer = document.querySelector('.matrix-container') as HTMLElement
      if (matrixContainer && matrixContainer.offsetWidth > 0) {
        targetElement = matrixContainer
      }
    }
    
    if (!targetElement) {
      const tables = document.querySelectorAll('table')
      for (const table of tables) {
        const htmlTable = table as HTMLElement
        if (htmlTable.offsetWidth > 0) {
          targetElement = htmlTable
          break
        }
      }
    }
    
    if (!targetElement) {
      console.error('No valid element found')
      alert('Matrix table not found')
      if (button) button.textContent = 'Download Matrix as Image'
      return
    }
    
    // 性能ヘッダーとステークホルダー名の両方を処理
    const verticalElements = targetElement.querySelectorAll('.performance-header, .stakeholder-name-vertical')
    const originalVisibility: { element: HTMLElement; visibility: string; color: string }[] = []

    verticalElements.forEach(el => {
      const htmlEl = el as HTMLElement
      const computedStyle = window.getComputedStyle(htmlEl)
      originalVisibility.push({
        element: htmlEl,
        visibility: computedStyle.visibility,
        color: computedStyle.color
      })
      htmlEl.style.color = 'transparent'
    })
    
    const html2canvas = (await import('html2canvas')).default as any
    const baseCanvas = await html2canvas(targetElement, {
      scale: 2,
      backgroundColor: '#ffffff',
      logging: false,
      useCORS: true,
      allowTaint: true,
      ignoreElements: (element: HTMLElement) => {
        return element.tagName === 'CANVAS' && element.getAttribute('data-engine')?.includes('three.js')
      }
    })
    
    originalVisibility.forEach(({ element, visibility, color }) => {
      element.style.visibility = visibility
      element.style.color = color
    })
    if (baseCanvas.width === 0 || baseCanvas.height === 0) {
      alert('Failed to generate image (size is 0)')
      if (button) button.textContent = 'Download Matrix as Image'
      return
    }
    
    const finalCanvas = document.createElement('canvas')
    finalCanvas.width = baseCanvas.width
    finalCanvas.height = baseCanvas.height
    const ctx = finalCanvas.getContext('2d')
    
    if (!ctx) {
      alert('Failed to get canvas context')
      if (button) button.textContent = 'Download Matrix as Image'
      return
    }
    
    ctx.drawImage(baseCanvas, 0, 0)
    
    const tableRect = targetElement.getBoundingClientRect()
    const scrollLeft = targetElement.scrollLeft || 0
    const scrollTop = targetElement.scrollTop || 0
    
    verticalElements.forEach(el => {
      const htmlEl = el as HTMLElement
      
      // ステークホルダー名の場合は親要素から位置を取得
      const isStakeholderName = htmlEl.classList.contains('stakeholder-name-vertical')
      const targetEl = isStakeholderName ? htmlEl.closest('.stakeholder-header') as HTMLElement : htmlEl
      
      if (!targetEl) return
      
      const rect = targetEl.getBoundingClientRect()
      const computedStyle = window.getComputedStyle(targetEl)
      
      const x = (rect.left - tableRect.left + scrollLeft) * 2
      const y = (rect.top - tableRect.top + scrollTop) * 2
      const width = rect.width * 2
      const height = rect.height * 2
      
      // 性能ヘッダーの場合のみ背景を描画
      if (htmlEl.classList.contains('performance-header')) {
        const bgColor = computedStyle.backgroundColor
        ctx.fillStyle = bgColor
        ctx.fillRect(x, y, width, height)
        
        ctx.strokeStyle = '#dee2e6'
        ctx.lineWidth = 1
        ctx.strokeRect(x, y, width, height)
        
        if (htmlEl.classList.contains('is-leaf')) {
          const borderColor = computedStyle.borderTopColor || computedStyle.borderColor
          ctx.strokeStyle = borderColor
          ctx.lineWidth = 4
          ctx.strokeRect(x + 2, y + 2, width - 4, height - 4)
        }
      }
      
      const text = htmlEl.textContent?.trim() || ''
      if (text) {
        // ステークホルダー名の場合は、votes部分を除外して上部に配置
        if (isStakeholderName) {
          const adjustedHeight = height * 0.8 // votesのスペースを除外
          drawVerticalText(ctx, text, x, y, width, adjustedHeight)
        } else {
          drawVerticalText(ctx, text, x, y, width, height)
        }
      }
    })
    finalCanvas.toBlob((blob: Blob | null) => {
      if (!blob) {
        alert('Failed to create image data')
        return
      }
      
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `Integrated_Matrix_${new Date().toISOString().slice(0, 10)}.png`
      link.click()
      URL.revokeObjectURL(url)
      
    }, 'image/png', 0.95)
    
    if (button) {
      button.textContent = 'Download Matrix as Image'
    }
    
  } catch (error) {
    console.error('Image generation error:', error)
    alert(`Failed to generate image: ${error}`)
    
    const button = document.querySelector('.matrix-image-button span')
    if (button) {
      button.textContent = 'Download Matrix as Image'
    }
  }
}

function drawVerticalText(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  width: number,
  height: number
) {
  const maxFontSize = 28
  const minFontSize = 16
  const size = Math.max(minFontSize, Math.min(maxFontSize, width * 0.6))
  const kerning = 0.7
  
  const subCanvas = document.createElement('canvas')
  const subCtx = subCanvas.getContext('2d')
  if (!subCtx) return
  
  const textHeight = size * kerning * text.length + (size * (1 - kerning))
  
  const startX = x + (width - size) / 2
  const startY = y + Math.max(8, (height - textHeight) / 2)
  
  ;[...text].forEach((char, i) => {
    subCanvas.width = subCanvas.height = size * 2
    subCtx.clearRect(0, 0, subCanvas.width, subCanvas.height)
    subCtx.textAlign = 'center'
    subCtx.textBaseline = 'middle'
    subCtx.font = `bold ${size}px sans-serif`
    subCtx.fillStyle = '#495057'
    
    if (char === 'ー') {
      subCtx.translate(size, size)
      subCtx.rotate(90 * Math.PI / 180)
      subCtx.translate(-size, -size)
    }
    
    subCtx.fillText(char, size, size)
    
    if (char === 'ー') {
      subCtx.translate(size, size)
      subCtx.rotate(-90 * Math.PI / 180)
      subCtx.translate(-size, -size)
    }
    
    ctx.drawImage(subCanvas, startX, startY + size * kerning * i, size, size)
  })
}

function downloadMatrixAsExcel() {
  const wb = XLSX.utils.book_new()
  
  const matrixData: (string | number)[][] = []
  
  const perfColumns = getAllPerformanceColumns()
  
  const headerRow1: (string | number)[] = ['Needs']
  stakeholders.value.forEach(() => headerRow1.push(''))
  headerRow1.push('Total Votes')
  perfColumns.forEach(() => headerRow1.push(''))
  matrixData.push(headerRow1)
  
  for (let level = 1; level <= maxPerformanceLevel.value; level++) {
    const levelRow: (string | number)[] = []
    
    if (level === 1) {
      levelRow.push('') 
      stakeholders.value.forEach(sh => levelRow.push(`${sh.name} (${sh.votes})`))
      levelRow.push('') 
    } else {
      levelRow.push('')
      stakeholders.value.forEach(() => levelRow.push(''))
      levelRow.push('')
    }
    
    const cellsAtLevel = getMatrixCellsAtLevel(level)
    cellsAtLevel.forEach(cell => {
      const displayName = cell.performance.unit 
        ? `${cell.performance.name} (${cell.performance.unit})` 
        : cell.performance.name
      levelRow.push(displayName)
      
      for (let i = 1; i < cell.colspan; i++) {
        levelRow.push('')
      }
    })
    
    matrixData.push(levelRow)
  }
  
  needs.value.forEach(need => {
    const row: (string | number)[] = [need.name]
    
    stakeholders.value.forEach(sh => {
      const votes = getStakeholderVotesForNeed(sh.id, need.id)
      row.push(hasStakeholderRelation(sh.id, need.id) ? votes.toFixed(1) : '')
    })
    
    row.push(getRawTotalVotesForNeed(need.id).toFixed(1))
    
    perfColumns.forEach(perf => {
      if (perf.is_leaf) {
        const symbol = getPerformanceRelationSymbol(need.id, perf.id)
        const votes = getPerformanceVotesForNeed(need.id, perf.id)
        row.push(symbol ? `${symbol} ${votes.toFixed(1)}` : '')
      } else {
        row.push('-')
      }
    })
    
    matrixData.push(row)
  })
  
  const upVotesRow: (string | number)[] = ['↑Votes']
  stakeholders.value.forEach(() => upVotesRow.push(''))
  upVotesRow.push('')
  perfColumns.forEach(perf => {
    upVotesRow.push(perf.is_leaf ? getUpVotesForPerformance(perf.id).toFixed(1) : '')
  })
  matrixData.push(upVotesRow)
  
  const downVotesRow: (string | number)[] = ['↓Votes']
  stakeholders.value.forEach(() => downVotesRow.push(''))
  downVotesRow.push('')
  perfColumns.forEach(perf => {
    downVotesRow.push(perf.is_leaf ? getDownVotesForPerformance(perf.id).toFixed(1) : '')
  })
  matrixData.push(downVotesRow)
  
  const effectiveVotesRow: (string | number)[] = ['Valid Votes']
  stakeholders.value.forEach(() => effectiveVotesRow.push(''))
  effectiveVotesRow.push('')
  perfColumns.forEach(perf => {
    effectiveVotesRow.push(perf.is_leaf ? getNormalizedEffectiveVotesForPerformance(perf.id).toFixed(3) : '')
  })
  matrixData.push(effectiveVotesRow)
  
  const pValueRow: (string | number)[] = ['p= Σv_i / V']
  stakeholders.value.forEach(() => pValueRow.push(''))
  pValueRow.push('')
  perfColumns.forEach(perf => {
    pValueRow.push(perf.is_leaf ? getPValueForPerformance(perf.id).toFixed(4) : '')
  })
  matrixData.push(pValueRow)
  
  const pSquaredRow: (string | number)[] = ['p²']
  stakeholders.value.forEach(() => pSquaredRow.push(''))
  pSquaredRow.push('')
  perfColumns.forEach(perf => {
    pSquaredRow.push(perf.is_leaf ? getPSquaredForPerformance(perf.id).toFixed(4) : '')
  })
  matrixData.push(pSquaredRow)
  
  // HHIの行を追加
  const hhiRow: (string | number)[] = ['HHI = Σp²']
  stakeholders.value.forEach(() => hhiRow.push(''))
  hhiRow.push('')
  
  // ルートグループごとにHHIを計算して配置
  let currentIndex = 0
  rootGroups.value.forEach(group => {
    const hhi = getHHIForRoot(group.rootIndex)
    hhiRow.push(hhi.toFixed(4))
    
    // colspanに対応するため、残りのセルは空白
    for (let i = 1; i < group.colspan; i++) {
      hhiRow.push('')
    }
    currentIndex += group.colspan
  })
  
  // 残りのセル（rootGroupsに含まれない場合）も空白で埋める
  while (hhiRow.length < matrixData[0].length) {
    hhiRow.push('')
  }
  
  matrixData.push(hhiRow)
  
  const ws = XLSX.utils.aoa_to_sheet(matrixData)
  
  const columnWidths = matrixData[0].map((_, colIndex) => {
    const maxLength = Math.max(
      ...matrixData.map(row => {
        const cell = row[colIndex]
        return cell ? String(cell).length : 0
      })
    )
    return { wch: Math.min(maxLength + 2, 30) }
  })
  ws['!cols'] = columnWidths
  
  XLSX.utils.book_append_sheet(wb, ws, 'Integrated Matrix')
  
  const filename = `Integrated_Matrix_${new Date().toISOString().slice(0, 10)}.xlsx`
  XLSX.writeFile(wb, filename)
}
function handlePasteUtilityFunction() {
  if (!currentUtilityEdit.value || !copiedUtilityFunction.value) return
  
  if (currentUtilityEdit.value.performanceId !== copiedUtilityFunction.value.performanceId) {
    console.warn('Cannot paste to different performance')
    return
  }
  
  currentUtilityEdit.value.type = copiedUtilityFunction.value.type
  utilityPoints.value = copiedUtilityFunction.value.points.map(p => ({ ...p }))
  discreteRows.value = copiedUtilityFunction.value.discreteMapping.map(row => ({ ...row }))
  axisRange.value = { ...copiedUtilityFunction.value.axisRange }
  interpolationType.value = copiedUtilityFunction.value.interpolationType
  
  if (currentUtilityEdit.value.type === 'continuous') {
    nextTick(() => {
      initRangeSlider()
    })
  }
  
}

function hasUtilityFunction(): boolean {
  if (!currentUtilityEdit.value) return false
  
  if (currentUtilityEdit.value.type === 'continuous') {
    return utilityPoints.value.length > 0
  } else {
    return discreteRows.value.some(row => row.label !== '' || row.value !== 0)
  }
}

function canPasteUtilityFunction(): boolean {
  if (!currentUtilityEdit.value || !copiedUtilityFunction.value) return false
  return currentUtilityEdit.value.performanceId === copiedUtilityFunction.value.performanceId
}

function handleGraphClick(event: MouseEvent) {
  const svg = event.currentTarget as SVGElement
  const rect = svg.getBoundingClientRect()
  
  const svgX = ((event.clientX - rect.left) / rect.width) * 420
  const svgY = ((event.clientY - rect.top) / rect.height) * 330
  
  if (svgX < 50 || svgX > 380 || svgY < 20 || svgY > 280) {
    return
  }
  
  if (currentUtilityEdit.value?.type === 'continuous') {
    const valueX = ((svgX - 50) / 330) * (axisRange.value.max - axisRange.value.min) + axisRange.value.min
    const valueY = 1 - ((svgY - 20) / 260)
    
    utilityPoints.value.push({
      x: svgX,
      y: svgY,
      valueX: valueX,
      valueY: Math.max(0, Math.min(1, valueY))
    })
    
    utilityPoints.value.sort((a, b) => a.valueX - b.valueX)
  } else {
    if (discreteRows.value.length === 0) return
    
    let closestIndex = 0
    let minDistance = Infinity
    
    for (let i = 0; i < discreteRows.value.length; i++) {
      const x = getDiscreteXPosition(i)
      const distance = Math.abs(x - svgX)
      if (distance < minDistance) {
        minDistance = distance
        closestIndex = i
      }
    }
    
    const valueY = 1 - ((svgY - 20) / 260)
    discreteRows.value[closestIndex].value = Math.max(0, Math.min(1, valueY))
  }
}

function getDiscreteXPosition(index: number): number {
  if (discreteRows.value.length <= 1) {
    return 215 
  }
  const spacing = 330 / (discreteRows.value.length - 1)
  return 50 + index * spacing
}

const discreteGraphPoints = computed(() => {
  if (currentUtilityEdit.value?.type !== 'discrete') return []
  
  return discreteRows.value.map((row, index) => ({
    x: getDiscreteXPosition(index),
    y: 20 + (1 - row.value) * 260,
    valueX: index,
    valueY: row.value,
    label: row.label
  }))
})

function removePoint(index: number) {
  utilityPoints.value.splice(index, 1)
}

function showTooltip(point: UtilityPoint, event: MouseEvent) {
  const target = event.currentTarget as SVGElement
  const svg = target.closest('svg')
  if (!svg) return
  
  const rect = svg.getBoundingClientRect()
  
  tooltip.value = {
    visible: true,
    x: event.clientX - rect.left,
    y: event.clientY - rect.top - 10,
    content: `X: ${point.valueX.toFixed(2)}, Y: ${point.valueY.toFixed(3)}`
  }
}

function showDiscreteTooltip(point: any, index: number, event: MouseEvent) {
  const target = event.currentTarget as SVGElement
  const svg = target.closest('svg')
  if (!svg) return
  
  const rect = svg.getBoundingClientRect()
  
  tooltip.value = {
    visible: true,
    x: event.clientX - rect.left,
    y: event.clientY - rect.top - 10,
    content: `${point.label || '#' + (index + 1)}: ${point.valueY.toFixed(3)}`
  }
}

function hideTooltip() {
  tooltip.value.visible = false
}

function getPolylinePoints(): string {
  if (utilityPoints.value.length < 2) return ''
  
  if (interpolationType.value === 'linear') {
    return utilityPoints.value.map(p => `${p.x},${p.y}`).join(' ')
  } else if (interpolationType.value === 'step') {
    const points: string[] = []
    for (let i = 0; i < utilityPoints.value.length; i++) {
      const current = utilityPoints.value[i]
      points.push(`${current.x},${current.y}`)
      
      if (i < utilityPoints.value.length - 1) {
        const next = utilityPoints.value[i + 1]
        points.push(`${next.x},${current.y}`)
      }
    }
    return points.join(' ')
  } else {
    return utilityPoints.value.map(p => `${p.x},${p.y}`).join(' ')
  }
}

function getSmoothPath(): string {
  if (utilityPoints.value.length < 2) return ''
  
  const points = utilityPoints.value
  if (points.length === 2) {
    return `M ${points[0].x},${points[0].y} L ${points[1].x},${points[1].y}`
  }
  
  let path = `M ${points[0].x},${points[0].y}`
  
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[Math.max(0, i - 1)]
    const p1 = points[i]
    const p2 = points[i + 1]
    const p3 = points[Math.min(points.length - 1, i + 2)]
    
    const cp1x = p1.x + (p2.x - p0.x) / 6
    const cp1y = p1.y + (p2.y - p0.y) / 6
    const cp2x = p2.x - (p3.x - p1.x) / 6
    const cp2y = p2.y - (p3.y - p1.y) / 6
    
    path += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${p2.x},${p2.y}`
  }
  
  return path
}

function sliderToValue(sliderPos: number): number {
  const absPos = Math.abs(sliderPos)
  const sign = sliderPos >= 0 ? 1 : -1
  
  if (absPos <= 20) return sign * absPos * 0.1 
  if (absPos <= 40) return sign * (2 + (absPos - 20)) 
  if (absPos <= 60) return sign * (22 + (absPos - 40) * 5) 
  if (absPos <= 80) return sign * (122 + (absPos - 60) * 50) 
  return sign * (1122 + (absPos - 80) * 500) 
}

function valueToSlider(value: number): number {
  const absValue = Math.abs(value)
  const sign = value >= 0 ? 1 : -1
  
  if (absValue <= 2) return sign * Math.round(absValue / 0.1)
  if (absValue <= 22) return sign * (20 + Math.round(absValue - 2))
  if (absValue <= 122) return sign * (40 + Math.round((absValue - 22) / 5))
  if (absValue <= 1122) return sign * (60 + Math.round((absValue - 122) / 50))
  return sign * (80 + Math.round((absValue - 1122) / 500))
}

function initRangeSlider() {
  if (!rangeSliderElement.value) {
    console.warn('rangeSliderElement is not available')
    return
  }
  
  if (rangeSliderInstance) {
    try {
      rangeSliderInstance.destroy()
    } catch (e) {
      console.warn('Failed to destroy existing slider:', e)
    }
    rangeSliderInstance = null
  }
  
  const minSliderPos = valueToSlider(axisRange.value.min)
  const maxSliderPos = valueToSlider(axisRange.value.max)
  
  try {
    rangeSliderInstance = noUiSlider.create(rangeSliderElement.value, {
      start: [minSliderPos, maxSliderPos],
      connect: true,
      range: {
        'min': -100,
        'max': 100
      },
      step: 1,
      tooltips: [
        { to: (value) => sliderToValue(value).toFixed(2) },
        { to: (value) => sliderToValue(value).toFixed(2) }
      ]
    })
    
    rangeSliderInstance.on('update', (values: any) => {
      const [minPos, maxPos] = values.map(Number)
      axisRange.value.min = sliderToValue(minPos)
      axisRange.value.max = sliderToValue(maxPos)
      updatePointCoordinates()
    })
  } catch (e) {
    console.error('Failed to create noUiSlider:', e)
  }
}

function updatePointCoordinates() {
  utilityPoints.value = utilityPoints.value.map(p => {
    const x = 50 + ((p.valueX - axisRange.value.min) / (axisRange.value.max - axisRange.value.min)) * 330
    const y = 20 + (1 - p.valueY) * 260
    return {
      x: Math.max(50, Math.min(380, x)), 
      y,
      valueX: p.valueX,
      valueY: p.valueY
    }
  })
}

function updateRangeFromInput() {
  if (axisRange.value.min >= axisRange.value.max) {
    axisRange.value.min = axisRange.value.max - 0.01
  }
  
  if (rangeSliderInstance) {
    const minSliderPos = valueToSlider(axisRange.value.min)
    const maxSliderPos = valueToSlider(axisRange.value.max)
    rangeSliderInstance.set([minSliderPos, maxSliderPos])
  }
  
  updatePointCoordinates()
}

function switchToType(type: 'continuous' | 'discrete') {
  if (!currentUtilityEdit.value) return
  
  currentUtilityEdit.value.type = type
  
  if (type === 'continuous') {
    nextTick(() => {
      initRangeSlider()
    })
  }
}

const validPerformanceIds = computed(() => {
  return new Set(performances.value.map(p => p.id))
})

const validNeedPerformanceRelations = computed(() => {
  return needPerformanceRelations.value.filter(r => 
    validPerformanceIds.value.has(r.performance_id)
  )
})

const maxPerformanceLevel = computed(() => {
  if (performances.value.length === 0) return 0
  return Math.max(...performances.value.map(p => p.level)) + 1
})

const uncheckedNeedIds = computed(() => {
  const leafPerformanceIds = new Set(
    performances.value.filter(p => p.is_leaf).map(p => p.id)
  )
  
  const checkedNeedIds = new Set<string>()
  validNeedPerformanceRelations.value.forEach(r => {
    if (leafPerformanceIds.has(r.performance_id)) {
      checkedNeedIds.add(r.need_id)
    }
  })
  
  return new Set(needs.value.filter(n => !checkedNeedIds.has(n.id)).map(n => n.id))
})

const uncheckedPerformanceIds = computed(() => {
  const leafPerformanceIds = new Set(
    performances.value.filter(p => p.is_leaf).map(p => p.id)
  )
  
  const checkedPerformanceIds = new Set<string>()
  validNeedPerformanceRelations.value.forEach(r => {
    if (leafPerformanceIds.has(r.performance_id)) {
      checkedPerformanceIds.add(r.performance_id)
    }
  })
  
  return new Set(
    performances.value
      .filter(p => p.is_leaf && !checkedPerformanceIds.has(p.id))
      .map(p => p.id)
  )
})

interface MatrixCell {
  performance: Performance
  colspan: number
  rowspan: number
  isVisible: boolean
}

const performanceMatrix = computed(() => {
  if (performances.value.length === 0) return []
  
  const maxLevel = maxPerformanceLevel.value
  const matrix: MatrixCell[][] = []
  
  for (let i = 0; i < maxLevel; i++) {
    matrix.push([])
  }
  
  function countLeafColumns(perf: Performance): number {
    if (perf.is_leaf) return 1
    const children = performances.value.filter(p => p.parent_id === perf.id)
    if (children.length === 0) return 1
    return children.reduce((sum, child) => sum + countLeafColumns(child), 0)
  }
  
  function buildMatrix(perf: Performance, level: number) {
    const leafCount = countLeafColumns(perf)
    const children = performances.value.filter(p => p.parent_id === perf.id)
    
    const rowspan = perf.is_leaf ? (maxLevel - level) : 1
    
    matrix[level].push({
      performance: perf,
      colspan: leafCount,
      rowspan: rowspan,
      isVisible: true
    })
    
    if (children.length > 0) {
      children.forEach(child => buildMatrix(child, level + 1))
    }
  }
  
  const roots = performances.value.filter(p => !p.parent_id || p.parent_id === null)
  roots.forEach(root => buildMatrix(root, 0))
  
  return matrix
})

function getMatrixCellsAtLevel(level: number): MatrixCell[] {
  if (level < 1 || level > performanceMatrix.value.length) return []
  return performanceMatrix.value[level - 1]
}

function getAllPerformanceColumns(): Performance[] {
  const result: Performance[] = []
  
  function collectLeaves(parentId: string | null | undefined) {
    const children = performances.value.filter(p => p.parent_id === parentId)
    
    for (const child of children) {
      if (child.is_leaf) {
        result.push(child)
      } else {
        collectLeaves(child.id)
      }
    }
  }
  
  collectLeaves(null)
  collectLeaves(undefined)
  
  return result
}

function getRootIndexForPerformance(performanceId: string): number {
  const roots = performances.value.filter(p => !p.parent_id || p.parent_id === null)
  
  function findRoot(perf: Performance): Performance {
    if (!perf.parent_id) return perf
    const parent = performances.value.find(p => p.id === perf.parent_id)
    if (!parent) return perf
    return findRoot(parent)
  }
  
  const performance = performances.value.find(p => p.id === performanceId)
  if (!performance) return 0
  
  const root = findRoot(performance)
  const index = roots.findIndex(r => r.id === root.id)
  return index >= 0 ? index : 0
}

interface RootGroup {
  rootIndex: number
  rootPerformance: Performance
  leafPerformances: Performance[]
  colspan: number
}

const rootGroups = computed((): RootGroup[] => {
  const roots = performances.value.filter(p => !p.parent_id || p.parent_id === null)
  const allLeafPerformances = getAllPerformanceColumns()
  
  return roots.map((root, index) => {
    const leafPerformances = allLeafPerformances.filter(
      leaf => getRootIndexForPerformance(leaf.id) === index
    )
    
    return {
      rootIndex: index,
      rootPerformance: root,
      leafPerformances: leafPerformances,
      colspan: leafPerformances.length
    }
  })
})

function getEffectiveVotesForRoot(rootIndex: number): number {
  const group = rootGroups.value.find(g => g.rootIndex === rootIndex)
  if (!group) return 0
  
  let total = 0
  group.leafPerformances.forEach(perf => {
    total += getEffectiveVotesForPerformance(perf.id)
  })
  
  return total
}

function getPValueForPerformance(performanceId: string): number {
  const rootIndex = getRootIndexForPerformance(performanceId)
  const V = getEffectiveVotesForRoot(rootIndex)
  
  if (V === 0) return 0
  
  const effectiveVotes = getEffectiveVotesForPerformance(performanceId)
  return effectiveVotes / V
}

function getPSquaredForPerformance(performanceId: string): number {
  const p = getPValueForPerformance(performanceId)
  return p * p
}

function getHHIForRoot(rootIndex: number): number {
  const group = rootGroups.value.find(g => g.rootIndex === rootIndex)
  if (!group) return 0
  
  let sum = 0
  group.leafPerformances.forEach(perf => {
    sum += getPSquaredForPerformance(perf.id)
  })
  
  return sum
}

const pSquaredValues = computed(() => {
  return getAllPerformanceColumns().map(perf => getPSquaredForPerformance(perf.id))
})

const pSquaredMin = computed(() => Math.min(...pSquaredValues.value.filter(v => v > 0)))
const pSquaredMax = computed(() => Math.max(...pSquaredValues.value))

const hhiValues = computed(() => {
  return rootGroups.value.map(group => getHHIForRoot(group.rootIndex))
})

const hhiMin = computed(() => Math.min(...hhiValues.value.filter(v => v > 0)))
const hhiMax = computed(() => Math.max(...hhiValues.value))

function getColorScaleGreenYellowRed(value: number, min: number, max: number): string {
  if (value === 0 || max === min) return 'rgb(255, 255, 255)'
  
  const normalized = (value - min) / (max - min)
  
  let r, g, b
  if (normalized > 0.5) {
    const t = (normalized - 0.5) * 2
    r = Math.round(255 - 24 * t) 
    g = Math.round(235 - 121 * t) 
    b = Math.round(59 - 52 * (1 - t) * t + 52)
  } else {
    const t = normalized * 2
    r = Math.round(99 + 156 * t)
    g = Math.round(190 + 45 * t) 
    b = Math.round(123 - 64 * t) 
  }
  
  return `rgb(${r}, ${g}, ${b})`
}

function hasStakeholderRelation(stakeholderId: string, needId: string): boolean {
  return stakeholderNeedRelations.value.some(
    r => r.stakeholder_id === stakeholderId && r.need_id === needId
  )
}

function getStakeholderVotesForNeed(stakeholderId: string, needId: string): number {
  if (!hasStakeholderRelation(stakeholderId, needId)) {
    return 0
  }
  
  const stakeholder = stakeholders.value.find(s => s.id === stakeholderId)
  if (!stakeholder) return 0
  
  const relatedNeedsCount = stakeholderNeedRelations.value.filter(
    r => r.stakeholder_id === stakeholderId
  ).length
  
  if (relatedNeedsCount === 0) return 0
  
  return stakeholder.votes / relatedNeedsCount
}

// 優先度適用前の元の合計票数（表示用）
function getRawTotalVotesForNeed(needId: string): number {
  let total = 0

  stakeholders.value.forEach(stakeholder => {
    total += getStakeholderVotesForNeed(stakeholder.id, needId)
  })

  return total
}

// 優先度適用後の合計票数（計算用）
function getTotalVotesForNeed(needId: string): number {
  const rawTotal = getRawTotalVotesForNeed(needId)

  // 優先度を適用
  const need = needs.value.find(n => n.id === needId)
  const priority = need?.priority ?? 1.0

  return rawTotal * priority
}

function getPerformanceVotesForNeed(needId: string, performanceId: string): number {
  const relation = getPerformanceRelation(needId, performanceId)
  if (!relation) return 0
  
  const totalVotes = getTotalVotesForNeed(needId)
  if (totalVotes === 0) return 0
  
  const leafPerformanceIds = new Set(performances.value.filter(p => p.is_leaf).map(p => p.id))
  const relatedPerformancesCount = validNeedPerformanceRelations.value.filter(
    r => r.need_id === needId && leafPerformanceIds.has(r.performance_id)
  ).length
  
  if (relatedPerformancesCount === 0) return 0
  
  return totalVotes / relatedPerformancesCount
}

function getUpVotesForPerformance(performanceId: string): number {
  let total = 0
  
  validNeedPerformanceRelations.value.forEach(relation => {
    if (relation.performance_id === performanceId && relation.direction === 'up') {
      total += getPerformanceVotesForNeed(relation.need_id, performanceId)
    }
  })
  
  return total
}

function getDownVotesForPerformance(performanceId: string): number {
  let total = 0
  
  validNeedPerformanceRelations.value.forEach(relation => {
    if (relation.performance_id === performanceId && relation.direction === 'down') {
      total += getPerformanceVotesForNeed(relation.need_id, performanceId)
    }
  })
  
  return total
}

function calculateEntropy(x: number): number {
  if (x === 0 || x === 1) return 0
  return -x * Math.log2(x) - (1 - x) * Math.log2(1 - x)
}

function getEffectiveVotesForPerformance(performanceId: string): number {
  const upVotes = getUpVotesForPerformance(performanceId)
  const downVotes = getDownVotesForPerformance(performanceId)
  const total = upVotes + downVotes
  
  if (total === 0) return 0
  
  const x = upVotes / total
  const entropy = calculateEntropy(x)
  
  return total * (1 + entropy)
}

// 正規化されたValid Votesを計算
function getNormalizedEffectiveVotesForPerformance(performanceId: string): number {
  const effectiveVotes = getEffectiveVotesForPerformance(performanceId)
  
  // 全てのリーフパフォーマンスのEffective Votesの合計を計算
  let totalEffectiveVotes = 0
  getAllPerformanceColumns().forEach(perf => {
    if (perf.is_leaf) {
      totalEffectiveVotes += getEffectiveVotesForPerformance(perf.id)
    }
  })
  
  if (totalEffectiveVotes === 0) return 0
  
  return effectiveVotes / totalEffectiveVotes
}

async function toggleStakeholderRelation(stakeholderId: string, needId: string) {
  if (hasStakeholderRelation(stakeholderId, needId)) {
    await projectStore.removeStakeholderNeedRelation(stakeholderId, needId)
  } else {
    await projectStore.addStakeholderNeedRelation(stakeholderId, needId)
  }
}

async function updateNeedPriority(needId: string, event: Event) {
  const target = event.target as HTMLInputElement
  const priority = parseFloat(target.value)
  
  if (isNaN(priority) || priority < 0 || priority > 1) {
    // 無効な値の場合は元の値に戻す
    const need = needs.value.find(n => n.id === needId)
    if (need) {
      target.value = String(need.priority || 1.0)
    }
    return
  }
  
  const need = needs.value.find(n => n.id === needId)
  if (!need) return
  
  await projectStore.updateNeed(needId, {
    name: need.name,
    category: need.category,
    description: need.description,
    priority: priority
  })
}

function getPerformanceRelation(needId: string, performanceId: string) {
  return validNeedPerformanceRelations.value.find(
    r => r.need_id === needId && r.performance_id === performanceId
  )
}

function getPerformanceRelationSymbol(needId: string, performanceId: string): string {
  const relation = getPerformanceRelation(needId, performanceId)
  if (!relation) return ''
  return relation.direction === 'up' ? '↑' : '↓'
}

function getPerformanceRelationClass(needId: string, performanceId: string): string {
  const relation = getPerformanceRelation(needId, performanceId)
  if (!relation) return ''
  return relation.direction === 'up' ? 'direction-up' : 'direction-down'
}

function isUncheckedCell(needId: string, performanceId: string): boolean {
  return uncheckedNeedIds.value.has(needId) || uncheckedPerformanceIds.value.has(performanceId)
}

async function cyclePerformanceRelation(needId: string, performanceId: string) {
  const relation = getPerformanceRelation(needId, performanceId)
  const utility = getUtilityFunction(needId, performanceId)
  
  if (!relation) {
    await projectStore.addNeedPerformanceRelation(needId, performanceId, 'up')
    
    const archived = utilityFunctions.value.find(
      u => u.need_id === needId && u.performance_id === performanceId && u.archived
    )
    if (archived) {
      archived.archived = false
      archived.warning = true
      archived.direction = 'up'
    }
  } else if (relation.direction === 'up') {
    await projectStore.updateNeedPerformanceRelation(needId, performanceId, 'down')
    
    if (utility && utility.saved) {
      utility.warning = true
      utility.direction = 'down'
    }
  } else {
    await projectStore.removeNeedPerformanceRelation(needId, performanceId)
    
    if (utility && utility.saved) {
      utility.archived = true
      utility.warning = false
    }
  }
}

function navigateToPerformanceManagement() {
  emit('navigateToPerformance')
}

function getUtilityFunction(needId: string, performanceId: string): UtilityFunction | undefined {
  const result = utilityFunctions.value.find(
    u => u.need_id === needId && u.performance_id === performanceId && !u.archived
  )
  
  
  return result
}

function getUtilityButtonType(needId: string, performanceId: string): 'none' | 'add' | 'check' | 'warning' {
  const relation = getPerformanceRelation(needId, performanceId)
  if (!relation) return 'none'
  
  const utility = getUtilityFunction(needId, performanceId)
  if (!utility) return 'add'
  
  if (utility.warning) return 'warning'
  if (utility.saved) return 'check'
  return 'add'
}

async function openUtilityModal(needId: string, performanceId: string, event: Event) {
  event.stopPropagation()
  
  const buttonType = getUtilityButtonType(needId, performanceId)
  if (buttonType === 'none') return
  
  const sameColumnFunctions = utilityFunctions.value.filter(
    u => u.performance_id === performanceId && u.saved
  )
  
  const columnStandard = sameColumnFunctions.length > 0 ? sameColumnFunctions[0] : null
  
  let utility = getUtilityFunction(needId, performanceId)
  
  if (!utility) {
    try {
      const loadedUtility = await projectStore.getUtilityFunction(needId, performanceId)
      if (loadedUtility) {
        utility = loadedUtility
        utilityFunctions.value.push(loadedUtility)
      }
    } catch (error) {
      console.error('Failed to load utility function:', error)
    }
  }
  
  const effectiveType = columnStandard?.type || utility?.type || 'continuous'
  
  currentUtilityEdit.value = {
    needId,
    performanceId,
    type: effectiveType
  }
  
  if (effectiveType === 'continuous') {
    if (columnStandard?.axisMin !== undefined && columnStandard?.axisMax !== undefined) {
      axisRange.value = {
        min: columnStandard.axisMin,
        max: columnStandard.axisMax
      }
    } else if (utility?.axisMin !== undefined && utility?.axisMax !== undefined) {
      axisRange.value = {
        min: utility.axisMin,
        max: utility.axisMax
      }
    } else {
      axisRange.value = {
        min: 0,
        max: 100
      }
    }
  }
  
  if (utility?.points && utility.points.length > 0) {
    utilityPoints.value = utility.points.map(p => {
      const x = 50 + ((p.valueX - axisRange.value.min) / (axisRange.value.max - axisRange.value.min)) * 330
      const y = 20 + (1 - p.valueY) * 260
      return {
        x,
        y,
        valueX: p.valueX,
        valueY: p.valueY
      }
    })
  } else {
    utilityPoints.value = []
  }
  
  if (effectiveType === 'discrete') {
    if (columnStandard?.discreteRows && columnStandard.discreteRows.length > 0) {
      const standardLabels = columnStandard.discreteRows.map(r => r.label)
      
      if (utility?.discreteRows && utility.discreteRows.length > 0) {
        discreteRows.value = standardLabels.map(label => {
          const existing = utility.discreteRows?.find(r => r.label === label)
          return {
            label,
            value: existing?.value ?? 0
          }
        })
      } else {
        discreteRows.value = standardLabels.map(label => ({
          label,
          value: 0
        }))
      }
    } else if (utility?.discreteRows && utility.discreteRows.length > 0) {
      discreteRows.value = [...utility.discreteRows]
    } else {
      discreteRows.value = [{ label: '', value: 0 }]
    }
  }
  
  showUtilityModal.value = true
  
  document.body.style.overflow = 'hidden'
  
  nextTick(() => {
    if (currentUtilityEdit.value?.type === 'continuous') {
      initRangeSlider()
    }
  })
}

function closeUtilityModal() {
  showUtilityModal.value = false
  currentUtilityEdit.value = null
  utilityPoints.value = []
  discreteRows.value = [{ label: '', value: 0 }]
  
  document.body.style.overflow = ''
}

async function saveUtilityFunction() {
  if (!currentUtilityEdit.value) return
  
  const { needId, performanceId } = currentUtilityEdit.value
  const relation = getPerformanceRelation(needId, performanceId)
  if (!relation) return
  
  const sameColumnRelations = currentProject.value?.need_performance_relations.filter(
    r => r.performance_id === performanceId
  ) || []
  
  const utilityData: UtilityFunction = {
    need_id: needId,
    performance_id: performanceId,
    direction: relation.direction,
    type: currentUtilityEdit.value.type,
    axisMin: currentUtilityEdit.value.type === 'continuous' ? axisRange.value.min : undefined,
    axisMax: currentUtilityEdit.value.type === 'continuous' ? axisRange.value.max : undefined,
    points: currentUtilityEdit.value.type === 'continuous' ? [...utilityPoints.value] : [],
    discreteRows: currentUtilityEdit.value.type === 'discrete' ? [...discreteRows.value] : undefined,
    saved: true,
    warning: false,
    archived: false
  }
  
  try {
    await projectStore.saveUtilityFunction(needId, performanceId, utilityData)
    
    const existingIndex = utilityFunctions.value.findIndex(
      u => u.need_id === needId && u.performance_id === performanceId
    )
    
    if (existingIndex >= 0) {
      utilityFunctions.value[existingIndex] = utilityData
    } else {
      utilityFunctions.value.push(utilityData)
    }
    
    for (const rel of sameColumnRelations) {
      if (rel.need_id === needId) continue;
      
      const existingFunc = utilityFunctions.value.find(
        u => u.need_id === rel.need_id && u.performance_id === performanceId
      )
      
      if (existingFunc) {
        const updatedData: UtilityFunction = {
          ...existingFunc,
          axisMin: utilityData.axisMin,
          axisMax: utilityData.axisMax
        }
        
        await projectStore.saveUtilityFunction(rel.need_id, performanceId, updatedData)
        
        const idx = utilityFunctions.value.findIndex(
          u => u.need_id === rel.need_id && u.performance_id === performanceId
        )
        if (idx >= 0) {
          utilityFunctions.value[idx] = updatedData
        }
      }
    }
    
    closeUtilityModal()
  } catch (error) {
    console.error('Failed to save utility function:', error)
    alert('Failed to save utility function.')
  }
}

async function resetUtilityFunction() {
  if (!currentUtilityEdit.value) return
  
  if (!confirm('Reset utility function data? This operation cannot be undone.')) {
    return
  }
  
  const { needId, performanceId } = currentUtilityEdit.value
  
  try {
    const projectId = projectStore.currentProject?.id
    if (!projectId) {
      throw new Error('Cannot get project ID')
    }
    
    const response = await fetch(
      `http://localhost:8000/api/projects/${projectId}/utility-functions/${needId}/${performanceId}`,
      {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
    
    if (!response.ok) {
      throw new Error('Failed to delete')
    }
    
    const index = utilityFunctions.value.findIndex(
      u => u.need_id === needId && u.performance_id === performanceId
    )
    
    if (index >= 0) {
      utilityFunctions.value.splice(index, 1)
    }
    
    closeUtilityModal()
  } catch (error) {
    console.error('Failed to delete utility function:', error)
    alert('Failed to delete utility function.')
  }
}

function getCurrentPerformanceUnit(): string | undefined {
  if (!currentUtilityEdit.value) return undefined
  
  const performance = performances.value.find(
    p => p.id === currentUtilityEdit.value!.performanceId
  )
  
  return performance?.unit
}

async function loadAllUtilityFunctions() {
  if (!currentProject.value?.id) return
  
  try {
    const loadedFunctions = await projectStore.loadUtilityFunctions()
    utilityFunctions.value = loadedFunctions
    
    await normalizeUtilityFunctionsByColumn()
  } catch (error) {
    console.error('Failed to load utility functions:', error)
  }
}

async function normalizeUtilityFunctionsByColumn() {
  if (!currentProject.value) return
  
  const performanceGroups = new Map<string, typeof utilityFunctions.value>()
  
  utilityFunctions.value.forEach(uf => {
    if (!performanceGroups.has(uf.performance_id)) {
      performanceGroups.set(uf.performance_id, [])
    }
    performanceGroups.get(uf.performance_id)!.push(uf)
  })
  
  let totalNormalized = 0
  
  for (const [, functions] of performanceGroups.entries()) {
    if (functions.length <= 1) continue
    
    const standard = functions[0]
    
    for (let i = 1; i < functions.length; i++) {
      const func = functions[i]
      let needsUpdate = false
      
      if (standard.type === 'continuous' && func.type === 'continuous') {
        if (func.axisMin !== standard.axisMin || func.axisMax !== standard.axisMax) {
          func.axisMin = standard.axisMin
          func.axisMax = standard.axisMax
          needsUpdate = true
        }
      }
      
      if (standard.type === 'discrete' && func.type === 'discrete') {
        if (standard.discreteRows && func.discreteRows) {
          const standardLabels = standard.discreteRows.map(r => r.label).sort()
          const funcLabels = func.discreteRows.map(r => r.label).sort()
          
          if (JSON.stringify(standardLabels) !== JSON.stringify(funcLabels)) {
            const newRows = standard.discreteRows.map(sr => {
              const existing = func.discreteRows?.find(fr => fr.label === sr.label)
              return {
                label: sr.label,
                value: existing?.value ?? 0
              }
            })
            func.discreteRows = newRows
            needsUpdate = true
          }
        }
      }
      
      if (func.type !== standard.type) {
        func.type = standard.type
        func.axisMin = standard.axisMin
        func.axisMax = standard.axisMax
        func.discreteRows = standard.discreteRows ? [...standard.discreteRows.map(r => ({ ...r, value: 0 }))] : undefined
        needsUpdate = true
      }
      
      if (needsUpdate) {
        try {
          await projectStore.saveUtilityFunction(func.need_id, func.performance_id, func)
          totalNormalized++
        } catch (error) {
          console.error(`Failed to unify utility function: ${func.need_id} x ${func.performance_id}`, error)
        }
      }
    }
  }
  
  if (totalNormalized > 0) {
  }
}

watch(
  () => currentProject.value?.id,
  (newProjectId) => {
    if (newProjectId) {
      loadAllUtilityFunctions()
    } else {
      utilityFunctions.value = []
    }
  },
  { immediate: true }
)

const insufficientDecompositionAnalysis = computed(() => {
  const result = {
    rootLevel: [] as string[],
    leafLevel: [] as string[]
  }
  
  const rootAnalysis = rootGroups.value.map(group => ({
    name: group.rootPerformance.name,
    hhi: getHHIForRoot(group.rootIndex),
    isLeaf: group.rootPerformance.is_leaf
  })).filter(item => item.hhi > 0)
  
  rootAnalysis.sort((a, b) => b.hhi - a.hhi)
  
  const avgHHI = rootAnalysis.length > 0 
    ? rootAnalysis.reduce((sum, item) => sum + item.hhi, 0) / rootAnalysis.length 
    : 0
  
  const threshold = avgHHI
  const topCount = Math.max(1, Math.ceil(rootAnalysis.length * 0.5))
  result.rootLevel = rootAnalysis
    .filter(item => item.hhi >= threshold)
    .slice(0, Math.min(topCount, 5))
    .map(item => item.name)
  
  const leafAnalysis = getAllPerformanceColumns()
    .filter(perf => perf.is_leaf)
    .map(perf => ({
      name: perf.name,
      pSquared: getPSquaredForPerformance(perf.id)
    }))
    .filter(item => item.pSquared > 0)
  
  leafAnalysis.sort((a, b) => b.pSquared - a.pSquared)
  
  const avgPSquared = leafAnalysis.length > 0
    ? leafAnalysis.reduce((sum, item) => sum + item.pSquared, 0) / leafAnalysis.length
    : 0
  
  const pSquaredThreshold = avgPSquared
  const leafTopCount = Math.max(1, Math.ceil(leafAnalysis.length * 0.5))
  result.leafLevel = leafAnalysis
    .filter(item => item.pSquared >= pSquaredThreshold)
    .slice(0, Math.min(leafTopCount, 5))
    .map(item => item.name)
  
  return result
})

</script>

<style scoped lang="scss">
@use 'sass:color';
@import '../../style/color';
.need-performance-matrix {
  padding: 2vh;
}
/* Toolbar */
.matrix-toolbar {
  display: flex;
  gap: 1vw;
  margin-bottom: 3vh;
  padding: 1.5vh 1.5vw;
  background: color.scale($gray, $lightness: 5%);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.8vw;
  box-shadow: 0 0.3vh 1vh color.adjust($black, $alpha: -0.5);
}

.toolbar-button {
  display: flex;
  align-items: center;
  gap: 0.5vw;
  padding: 1.5vh 1.5vw;
  background: color.adjust($gray, $alpha: -0.3);
  border: 1px solid color.adjust($white, $alpha: -0.8);
  border-radius: 0.5vw;
  cursor: pointer;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  font-weight: 500;
  color: $white;
  transition: all 0.3s ease;
}

.toolbar-button:hover {
  background: color.adjust($gray, $alpha: -0.1);
  border-color: color.adjust($white, $alpha: -0.7);
  transform: translateY(-2px);
  box-shadow: 0 0.3vh 1vh color.adjust($main_1, $alpha: -0.6);
}

.toolbar-button .excel-icon {
  flex-shrink: 0;
}

.toolbar-button span {
  white-space: nowrap;
}

.toolbar-divider {
  width: 1px;
  align-self: stretch;
  background: color.adjust($white, $alpha: -0.85);
  margin: 0 0.5vw;
}

.template-download-button {
  background: linear-gradient(135deg, $sub_4, color.scale($sub_4, $lightness: -10%));
  border: none;
}

.template-download-button:hover {
  background: linear-gradient(135deg, color.scale($sub_4, $lightness: 5%), $sub_4);
  transform: translateY(-2px);
  box-shadow: 0 0.5vh 2vh color.adjust($sub_4, $alpha: -0.6);
}

.matrix-image-button {
  background: linear-gradient(135deg, $sub_6, color.scale($sub_6, $lightness: -10%));
  border: none;
}

.matrix-image-button:hover {
  background: linear-gradient(135deg, color.scale($sub_6, $lightness: 5%), $sub_6);
  transform: translateY(-2px);
  box-shadow: 0 0.5vh 2vh color.adjust($sub_6, $alpha: -0.6);
}

.matrix-excel-button {
  background: linear-gradient(135deg, #20744A, color.scale(#20744A, $lightness: -10%));
  border: none;
}

.matrix-excel-button:hover {
  background: linear-gradient(135deg, color.scale(#20744A, $lightness: 5%), #20744A);
  transform: translateY(-2px);
  box-shadow: 0 0.5vh 2vh color.adjust(#20744A, $alpha: -0.6);
}

.matrix-container {
  overflow-x: auto;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.matrix-table {
  width: auto;
  border-collapse: collapse;
  background: white;
  color: #333;
}

.corner-cell {
  background: #f5f5f5;
  padding: 16px;
  font-weight: 600;
  border: 1px solid #ddd;
  min-width: 150px;
  text-align: center;
  vertical-align: middle;
}

.group-header {
  padding: 12px;
  font-weight: 600;
  text-align: center;
  border: 1px solid #ddd;
  font-size: 15px;
}

.stakeholder-group {
  background: #667eea;
  color: white;
}

.total-votes-header {
  background: #f59e0b;
  color: white;
  font-weight: 700;
  min-width: 100px;
}

.priority-header {
  background: #10b981;
  color: white;
  font-weight: 700;
  min-width: 80px;
}

.performance-group {
  background: #764ba2;
  color: white;
}

.stakeholder-header {
  background: #e8eaf6;
  color: #333;
  padding: 10px 2px;
  border: 1px solid #ddd;
  min-width: 40px;
  text-align: center;
  vertical-align: middle;
  font-size: 13px;
}

.stakeholder-header-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  height: 100%;
  width: 100%;
}

.stakeholder-name-vertical {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  flex: 1;
  font-size: 13px;
  text-align: center;
  line-height: 1.2;
  display: inline-block;
  white-space: nowrap;
  -webkit-writing-mode: vertical-rl;
  -ms-writing-mode: tb-rl;
}

.stakeholder-votes-horizontal {
  writing-mode: horizontal-tb;
  font-size: 9px;
  font-weight: 600;
  color: #666;
  white-space: nowrap;
}

.performance-header {
  padding: 10px 2px;
  border: 1px solid #ddd;
  width: 28px;
  vertical-align: middle;
  text-align: center;
  font-size: 11px;
  writing-mode: vertical-rl;
  text-orientation: upright;
}

/* Root Category 0: Red Series */
.performance-header.root-0.level-1 {
  background: #ef9a9a;
}

.performance-header.root-0.level-2 {
  background: #ffcdd2;
}

.performance-header.root-0.level-3 {
  background: #ffebee;
}

/* Root Category 1: Blue Series */
.performance-header.root-1.level-1 {
  background: #90caf9;
}

.performance-header.root-1.level-2 {
  background: #bbdefb;
}

.performance-header.root-1.level-3 {
  background: #e3f2fd;
}

/* Root Category 2: Green Series */
.performance-header.root-2.level-1 {
  background: #a5d6a7;
}

.performance-header.root-2.level-2 {
  background: #c8e6c9;
}

.performance-header.root-2.level-3 {
  background: #e8f5e9;
}

/* Root Category 3: Yellow Series */
.performance-header.root-3.level-1 {
  background: #fff59d;
}

.performance-header.root-3.level-2 {
  background: #fff9c4;
}

.performance-header.root-3.level-3 {
  background: #fffde7;
}

/* Root Category 4: Purple Series */
.performance-header.root-4.level-1 {
  background: #e1bee7;
}

.performance-header.root-4.level-2 {
  background: #f3e5f5;
}

.performance-header.root-4.level-3 {
  background: #f8f5fa;
}

/* Root Category 5: Orange Series */
.performance-header.root-5.level-1 {
  background: #ffcc80;
}

.performance-header.root-5.level-2 {
  background: #ffe0b2;
}

.performance-header.root-5.level-3 {
  background: #fff3e0;
}

/* Root Category 6: Cyan Series */
.performance-header.root-6.level-1 {
  background: #80deea;
}

.performance-header.root-6.level-2 {
  background: #b2ebf2;
}

.performance-header.root-6.level-3 {
  background: #e0f7fa;
}

/* Root Category 7: Pink Series */
.performance-header.root-7.level-1 {
  background: #f48fb1;
}

.performance-header.root-7.level-2 {
  background: #f8bbd0;
}

.performance-header.root-7.level-3 {
  background: #fce4ec;
}

/* Fallback (for additional root categories) */
.performance-header.level-1 {
  background: #b0bec5;
}

.performance-header.level-2 {
  background: #cfd8dc;
}

.performance-header.level-3 {
  background: #eceff1;
}

/* Leaf cell borders: Default */
.performance-header.is-leaf {
  border: 2px solid #9c27b0;
  font-weight: 600;
}

/* Leaf cell borders: By root category */
.performance-header.root-0.is-leaf {
  border: 2px solid #c62828;
}

.performance-header.root-1.is-leaf {
  border: 2px solid #1565c0;
}

.performance-header.root-2.is-leaf {
  border: 2px solid #2e7d32;
}

.performance-header.root-3.is-leaf {
  border: 2px solid #f9a825;
}

.performance-header.root-4.is-leaf {
  border: 2px solid #9c27b0;
}

.performance-header.root-5.is-leaf {
  border: 2px solid #ef6c00;
}

.performance-header.root-6.is-leaf {
  border: 2px solid #00838f;
}

.performance-header.root-7.is-leaf {
  border: 2px solid #c2185b;
}

.header-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.votes-display {
  font-size: 9px;
  color: #666;
}

.unit-text {
  font-size: 9px;
  opacity: 0.8;
}

.leaf-badge {
  background: #9c27b0;
  color: white;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 9px;
  font-weight: 600;
}

.need-header {
  background: #f8f9fa;
  padding: 8px 10px;
  border: 1px solid #ddd;
  width: 100px;
  font-weight: 600;
  font-size: 12px;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.need-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.category-tag {
  background: #e0e0e0;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: normal;
}

.matrix-cell {
  border: 1px solid #ddd;
  padding: 6px 2px;
  text-align: center;
  width: 28px;
  min-height: 45px;
  transition: background-color 0.2s;
}

.stakeholder-cell {
  cursor: pointer;
}

.stakeholder-cell:hover {
  background: #f0f0f0;
}

.stakeholder-cell.active {
  background: #d4edda;
}

.total-votes-cell {
  background: #fef3c7;
  font-weight: 700;
  border-left: 3px solid #f59e0b;
  border-right: 3px solid #f59e0b;
}

.priority-cell {
  background: #d1fae5;
  padding: 4px;
  border-left: 2px solid #10b981;
  border-right: 2px solid #10b981;
}

.priority-input {
  width: 100%;
  min-width: 60px;
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  text-align: center;
  font-size: 14px;
  font-weight: 600;
}

.priority-input:focus {
  outline: none;
  border-color: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
}

.total-votes-value {
  color: #b45309;
  font-size: 18px;
}

.performance-cell.non-leaf {
  background: #fafafa;
  cursor: not-allowed;
}

.matrix-cell.unchecked {
  background-color: #fffbeb;
}

.performance-cell:not(.non-leaf) {
  cursor: pointer;
}

.performance-cell:not(.non-leaf):hover {
  background: #f0f0f0;
}

.performance-cell.direction-up {
  background: #d4edda;
}

.performance-cell.direction-down {
  background: #f8d7da;
}

.cell-content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: bold;
  height: 100%;
  gap: 2px;
}

.arrow-symbol {
  font-size: 18px;
  font-weight: bold;
}

.performance-votes {
  font-size: 10px;
  font-weight: 600;
  color: #666;
}

.stakeholder-cell.active .cell-content {
  color: #28a745;
}

.performance-cell.direction-up .arrow-symbol {
  color: #28a745;
}

.performance-cell.direction-down .arrow-symbol {
  color: #dc3545;
}

.non-leaf-indicator {
  color: #ccc;
  font-size: 16px;
}

.summary-row {
  background: #f8f9fa;
  border-top: 2px solid #6c757d;
}

.summary-empty {
  background: transparent;
  border: none;
}

.summary-label-cell {
  background: #e9ecef;
  padding: 10px 12px;
  font-weight: 600;
  font-size: 13px;
  color: #495057;
  border: 1px solid #ddd;
  text-align: center;
  min-width: 100px;
}

.effective-votes-label {
  background: #e9ecef;
  color: #495057;
  font-weight: 600;
}

.summary-cell {
  background: #ffffff;
  padding: 10px 8px;
  text-align: center;
  font-size: 14px;
  font-weight: 600;
  color: #495057;
  border: 1px solid #ddd;
}

.summary-value {
  font-size: 14px;
  font-weight: 700;
}

.effective-votes-row {
  border-top: 2px solid #6c757d;
  background: #f8f9fa;
}

.effective-votes-empty {
  background: transparent;
  border-top: 2px solid #6c757d;
}

.effective-votes-cell {
  background: #ffffff;
  color: #495057;
  font-weight: 600;
}

.effective-votes-cell .summary-value {
  font-size: 15px;
}

.root-summary-row {
  border-top: 2px solid #6c757d;
  background: #f8f9fa;
}

.root-summary-empty {
  background: transparent;
  border-top: 2px solid #6c757d;
}

.root-summary-label {
  background: #e9ecef;
  padding: 10px 12px;
  font-weight: 600;
  font-size: 13px;
  color: #495057;
  border: 1px solid #ddd;
  text-align: center;
  min-width: 100px;
}

.root-summary-cell {
  padding: 10px 8px;
  text-align: center;
  font-weight: 700;
  border: 2px solid #6c757d;
}

/* V row cell background colors: By root category (same colors as headers) */
.root-summary-cell.root-cell-0 {
  background: #ef9a9a;
  border: 2px solid #c62828;
}

.root-summary-cell.root-cell-1 {
  background: #90caf9;
  border: 2px solid #1565c0;
}

.root-summary-cell.root-cell-2 {
  background: #a5d6a7;
  border: 2px solid #2e7d32;
}

.root-summary-cell.root-cell-3 {
  background: #fff59d;
  border: 2px solid #f9a825;
}

.root-summary-cell.root-cell-4 {
  background: #e1bee7;
  border: 2px solid #9c27b0;
}

.root-summary-cell.root-cell-5 {
  background: #ffcc80;
  border: 2px solid #ef6c00;
}

.root-summary-cell.root-cell-6 {
  background: #80deea;
  border: 2px solid #00838f;
}

.root-summary-cell.root-cell-7 {
  background: #f48fb1;
  border: 2px solid #c2185b;
}

.root-value {
  font-size: 16px;
  font-weight: 700;
  color: #212529;
}

.p-value-row {
  border-top: 2px solid #6c757d;
  background: #f8f9fa;
}

.p-value-empty {
  background: transparent;
  border-top: 2px solid #6c757d;
}

.p-value-label {
  background: #e9ecef;
  padding: 10px 12px;
  font-weight: 600;
  font-size: 13px;
  color: #495057;
  border: 1px solid #ddd;
  text-align: center;
  min-width: 100px;
}

.p-value-cell {
  background: #ffffff;
  color: #495057;
  font-weight: 600;
  border: 1px solid #ddd;
}

.p-value-cell .summary-value {
  font-size: 13px;
}

.p-squared-row {
  border-top: 2px solid #6c757d;
  background: #f8f9fa;
}

.p-squared-empty {
  background: transparent;
  border-top: 2px solid #6c757d;
}

.p-squared-label {
  background: #e9ecef;
  padding: 10px 12px;
  font-weight: 600;
  font-size: 13px;
  color: #495057;
  border: 1px solid #ddd;
  text-align: center;
  min-width: 100px;
}

.p-squared-cell {
  color: #212529;
  font-weight: 700;
  border: 1px solid #ddd;
}

.p-squared-cell .summary-value {
  font-size: 12px;
  font-weight: 700;
}

.hhi-row {
  border-top: 3px solid #6c757d;
  background: #f8f9fa;
}

.hhi-empty {
  background: transparent;
  border-top: 3px solid #6c757d;
}

.hhi-label {
  background: #e9ecef;
  padding: 10px 12px;
  font-weight: 600;
  font-size: 13px;
  color: #495057;
  border: 1px solid #ddd;
  text-align: center;
  min-width: 100px;
}

.hhi-cell {
  color: #212529;
  font-weight: 700;
  border: 2px solid #ddd;
}

.hhi-value {
  font-size: 15px;
  font-weight: 700;
}
.empty-matrix {
  text-align: center;
  padding: 60px 20px;
  color: #999;
  background: #f8f9fa;
  border-radius: 8px;
}

/* Utility Function Button */
.utility-button {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 14px;
  height: 14px;
  border-radius: 3px;
  border: none;
  font-size: 10px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  pointer-events: auto;
  transition: all 0.2s ease;
  line-height: 1;
  padding: 0;
}

.utility-button-add {
  background: #3b82f6;
  color: white;
}

.utility-button-add:hover {
  background: #2563eb;
  transform: scale(1.1);
}

.utility-button-check {
  background: #10b981;
  color: white;
}

.utility-button-check:hover {
  background: #059669;
  transform: scale(1.1);
}

.utility-button-warning {
  background: #f59e0b;
  color: white;
  animation: pulse 2s infinite;
}

.utility-button-warning:hover {
  background: #d97706;
  transform: scale(1.1);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.cell-content {
  position: relative;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: color.adjust($black, $alpha: -0.2);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.modal-content {
  background: $gray;
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 1vw;
  padding: 3vh 3vw;
  max-width: 800px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 2vh 6vh color.adjust($black, $alpha: -0.5);
}

.utility-modal h3 {
  margin-bottom: 2.5vh;
  font-size: clamp(1.3rem, 1.8vw, 1.6rem);
  color: $white;
  font-weight: 600;
}

.modal-info {
  background: color.adjust($black, $alpha: -0.5);
  padding: 1.5vh 1.5vw;
  border-radius: 0.5vw;
  margin-bottom: 2vh;
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 13px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row strong {
  min-width: 60px;
  color: color.adjust($white, $alpha: -0.3);
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.graph-section {
  margin-bottom: 20px;
}

.graph-section label {
  display: block;
  margin-bottom: 0.8vh;
  font-weight: 600;
  color: $white;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
}

.graph-description {
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  color: color.adjust($white, $alpha: -0.4);
  margin-bottom: 1.5vh;
  font-style: italic;
}

.graph-container {
  background: color.adjust($black, $alpha: -0.3);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  padding: 1.5vh 1.5vw;
  box-shadow: inset 0 0.2vh 0.5vh color.adjust($black, $alpha: -0.7);
  max-width: 650px;
  margin: 0 auto;
}

.graph-controls {
  position: relative;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.graph-control-button {
  padding: 1vh 1vw;
  background: color.adjust($gray, $alpha: -0.3);
  border: 1px solid color.adjust($white, $alpha: -0.8);
  border-radius: 0.5vw;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $white;
}

.graph-control-button:hover {
  background: color.adjust($gray, $alpha: -0.1);
  border-color: color.adjust($white, $alpha: -0.7);
  transform: translateY(-2px);
}

.graph-control-button.copy-button {
  color: #0d6efd;
}

.graph-control-button.copy-button:hover {
  background: #e7f1ff;
  border-color: #0d6efd;
  color: #0a58ca;
}

.graph-control-button.camera-button {
  color: #6f42c1;
}

.graph-control-button.camera-button:hover {
  background: #f3e8ff;
  border-color: #6f42c1;
  color: #59359a;
}

.graph-control-button.import-button {
  color: #0dcaf0;
}

.graph-control-button.import-button:hover {
  background: #cff4fc;
  border-color: #0dcaf0;
  color: #087990;
}

.graph-control-button.excel-button {
  color: #107c41;
}

.graph-control-button.excel-button:hover {
  background: #d1f4e0;
  border-color: #107c41;
  color: #0b6631;
}

.graph-control-button.paste-button {
  color: #198754;
}

.graph-control-button.paste-button:hover {
  background: #d1f4e0;
  border-color: #198754;
  color: #146c43;
}

.graph-popup {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 1vh;
  background: $gray;
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  box-shadow: 0 0.5vh 1.5vh color.adjust($black, $alpha: -0.4);
  min-width: 280px;
  max-width: 320px;
  z-index: 1000;
  animation: popupFadeIn 0.2s ease;
}

@keyframes popupFadeIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e9ecef;
}

.popup-header h4 {
  margin: 0;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  font-weight: 600;
  color: $white;
}

.popup-close {
  background: none;
  border: none;
  font-size: 20px;
  color: #6c757d;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.popup-close:hover {
  background: #f8f9fa;
  color: #212529;
}

.popup-content {
  padding: 12px 16px;
}

.info-list {
  margin: 0;
  padding-left: 20px;
  list-style: none;
}

.info-list li {
  margin-bottom: 0.8vh;
  font-size: clamp(0.8rem, 0.95vw, 0.9rem);
  color: $white;
  line-height: 1.5;
  position: relative;
}

.info-list li::before {
  content: "▸";
  position: absolute;
  left: -16px;
  color: #3b82f6;
  font-weight: bold;
}

.info-list li:last-child {
  margin-bottom: 0;
}

.info-section-title {
  font-size: 12px;
  font-weight: 600;
  color: #212529;
  margin: 12px 0 8px 0;
  padding-left: 4px;
  border-left: 3px solid #3b82f6;
}

.info-section-title:first-child {
  margin-top: 0;
}

.setting-item {
  margin-bottom: 12px;
}

.setting-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #495057;
  margin-bottom: 6px;
}

.setting-select {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
  color: #495057;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s ease;
}

.setting-select:hover {
  border-color: #adb5bd;
}

.setting-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.setting-select:disabled {
  background: #e9ecef;
  color: #6c757d;
  cursor: not-allowed;
  opacity: 0.6;
}

.setting-description {
  font-size: 12px;
  color: #6c757d;
  font-style: italic;
  margin-top: 8px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.utility-graph {
  width: 100%;
  height: auto;
  display: block;
  cursor: crosshair;
}

.utility-point {
  transition: all 0.2s ease;
}

.utility-point:hover {
  r: 7;
  filter: drop-shadow(0 2px 4px rgba(59, 130, 246, 0.4));
}

.discrete-point:hover {
  filter: drop-shadow(0 2px 4px rgba(16, 185, 129, 0.4));
}

.custom-tooltip {
  pointer-events: none;
  animation: tooltipFadeIn 0.15s ease;
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.type-switcher {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 12px 0;
  margin-top: 8px;
}

.type-label {
  font-size: 14px;
  font-weight: 600;
  color: $white;
  margin-right: 4px;
}

.type-button {
  padding: 1.2vh 1.5vw;
  border: 1px solid color.adjust($white, $alpha: -0.8);
  border-radius: 0.5vw;
  background: color.adjust($gray, $alpha: -0.5);
  font-size: clamp(0.8rem, 0.95vw, 0.9rem);
  font-weight: 500;
  color: $white;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  gap: 0.5vw;
  align-items: center;
}

.type-button:hover {
  background: color.adjust($gray, $alpha: -0.3);
  border-color: color.adjust($white, $alpha: -0.7);
  transform: translateY(-2px);
}

.type-button.active {
  background: linear-gradient(135deg, $main_1, $main_2);
  border-color: $main_1;
  color: $white;
  box-shadow: 0 0.3vh 1vh color.adjust($main_1, $alpha: -0.6);
}

.type-icon {
  font-size: 10px;
  font-weight: bold;
}

.axis-range-control {
  margin-top: 2vh;
  padding: 2vh 2vw;
  background: color.adjust($black, $alpha: -0.5);
  border-radius: 0.5vw;
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.discrete-matrix-control {
  margin-top: 2vh;
  padding: 2vh 2vw;
  background: color.adjust($black, $alpha: -0.5);
  border-radius: 0.5vw;
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.matrix-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.matrix-label {
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  font-weight: 600;
  color: $white;
}

.add-row-button {
  padding: 1vh 1.2vw;
  background: linear-gradient(135deg, $main_1, $main_2);
  color: $white;
  border: none;
  border-radius: 0.5vw;
  font-size: clamp(0.8rem, 0.95vw, 0.9rem);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.add-row-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.3vh 1vh color.adjust($main_1, $alpha: -0.6);
}

.discrete-matrix {
  overflow-x: auto;
}

.discrete-table {
  width: 100%;
  border-collapse: collapse;
  background: color.adjust($black, $alpha: -0.7);
  border-radius: 0.5vw;
  overflow: hidden;
  border: 1px solid color.adjust($white, $alpha: -0.95);
}

.discrete-table thead {
  background: color.adjust($gray, $alpha: -0.3);
}

.discrete-table th {
  padding: 1vh 1.2vw;
  text-align: left;
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  font-weight: 600;
  color: $white;
  border-bottom: 1px solid color.adjust($white, $alpha: -0.9);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.label-column {
  width: 50%;
}

.value-column {
  width: 40%;
}

.action-column {
  width: 10%;
  text-align: center;
}

.discrete-row {
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
}

.discrete-row:last-child {
  border-bottom: none;
}

.discrete-row:hover {
  background: color.adjust($white, $alpha: -0.97);
}

.label-cell,
.value-cell,
.action-cell {
  padding: 8px 12px;
}

.discrete-input {
  width: 100%;
  padding: 1vh 1vw;
  background: color.adjust($black, $alpha: -0.3);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  color: $white;
  font-size: clamp(0.8rem, 0.95vw, 0.9rem);
  transition: all 0.3s ease;
}

.discrete-input:focus {
  outline: none;
  border-color: $main_1;
  background: color.adjust($black, $alpha: -0.1);
}

.remove-row-button {
  padding: 0.8vh 1vw;
  background: linear-gradient(135deg, $sub_1, color.scale($sub_1, $lightness: -10%));
  color: $white;
  border: none;
  border-radius: 0.4vw;
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  cursor: pointer;
  transition: all 0.3s ease;
}

.remove-row-button:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 0.2vh 0.5vh color.adjust($sub_1, $alpha: -0.6);
}

.remove-row-button:disabled {
  background: color.adjust($gray, $alpha: -0.5);
  color: color.adjust($white, $alpha: -0.6);
  cursor: not-allowed;
  opacity: 0.6;
}

.matrix-hint {
  margin-top: 1.5vh;
  padding: 1vh 1.2vw;
  background: color.adjust($main_1, $alpha: -0.9);
  border-left: 3px solid $main_1;
  border-radius: 0.4vw;
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  color: $white;
  line-height: 1.5;
  opacity: 0.9;
}

.range-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.range-label {
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  font-weight: 600;
  color: $white;
}

.range-tip {
  font-size: clamp(0.7rem, 0.85vw, 0.8rem);
  color: color.adjust($white, $alpha: -0.4);
  font-style: italic;
}

.range-single-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.range-input {
  padding: 1vh 1vw;
  background: color.adjust($black, $alpha: -0.3);
  border: 1px solid color.adjust($white, $alpha: -0.9);
  border-radius: 0.5vw;
  color: $white;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  font-weight: 500;
  width: 100px;
  transition: all 0.3s ease;
}

.range-input:focus {
  outline: none;
  border-color: $main_1;
  background: color.adjust($black, $alpha: -0.1);
}

.nouislider-container {
  flex: 1;
  height: 40px;
  display: flex;
  align-items: center;
}

/* Custom styles for noUiSlider */
.nouislider-container :deep(.noUi-target) {
  border: none;
  box-shadow: none;
  background: #dee2e6;
  height: 8px;
  border-radius: 4px;
}

.nouislider-container :deep(.noUi-connect) {
  background: #0066cc;
}

.nouislider-container :deep(.noUi-handle) {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 3px solid #0066cc;
  background: white;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  top: 50%;
  transform: translate(-50%, -50%);
}

.nouislider-container :deep(.noUi-handle:hover) {
  background: #f0f8ff;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
}

.nouislider-container :deep(.noUi-handle:before),
.nouislider-container :deep(.noUi-handle:after) {
  display: none;
}

.nouislider-container :deep(.noUi-tooltip) {
  background: #495057;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  padding: 4px 8px;
  bottom: 140%;
}

.modal-actions {
  display: flex;
  gap: 1vw;
  justify-content: flex-end;
  align-items: center;
  margin-top: 3vh;
}

.modal-actions .spacer {
  flex: 1;
}

.modal-actions button {
  padding: 1.5vh 2vw;
  border-radius: 0.5vw;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.modal-actions .secondary {
  background: color.adjust($gray, $alpha: -0.5);
  color: $white;
  border: 1px solid color.adjust($white, $alpha: -0.8);
}

.modal-actions .secondary:hover {
  background: color.adjust($gray, $alpha: -0.3);
  border-color: color.adjust($white, $alpha: -0.7);
}

.modal-actions .primary {
  background: linear-gradient(135deg, $main_1, $main_2);
  color: $white;
}

.modal-actions .primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5vh 2vh color.adjust($main_2, $alpha: -0.6);
}

.modal-actions .danger {
  background: linear-gradient(135deg, $sub_1, color.scale($sub_1, $lightness: -10%));
  color: $white;
}

.modal-actions .danger:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5vh 2vh color.adjust($sub_1, $alpha: -0.6);
}
</style>