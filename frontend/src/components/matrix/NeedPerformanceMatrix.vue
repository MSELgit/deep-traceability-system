<template>
  <div class="need-performance-matrix">
    <div class="section-header">
      <h2>統合マトリクス</h2>
    </div>

    <!-- ツールバー -->
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
        <span>効用関数のテンプレートファイルをダウンロード</span>
      </button>
      
      <div class="toolbar-divider"></div>
      
      <button class="toolbar-button matrix-image-button" @click="downloadMatrixAsImageVertical">
        <FontAwesomeIcon :icon="['fas', 'camera']" />
        <span>マトリクスを画像ダウンロード</span>
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
        <span>マトリクスをExcelダウンロード</span>
      </button>
    </div>

    <!-- 統合マトリクステーブル -->
    <div v-if="needs.length > 0 && (stakeholders.length > 0 || performances.length > 0)" class="matrix-container">
      <table class="matrix-table">
        <!-- ヘッダー: 階層的な性能列 -->
        <thead>
          <!-- 第1行: グループヘッダー -->
          <tr>
            <th :rowspan="maxPerformanceLevel + 1" class="corner-cell">ニーズ</th>
            <th :colspan="stakeholders.length" class="group-header stakeholder-group">
              ステークホルダー
            </th>
            <th :rowspan="maxPerformanceLevel + 1" class="group-header total-votes-header">
              合計票数
            </th>
            <th :colspan="getAllPerformanceColumns().length" class="group-header performance-group">
              性能（階層表示）
            </th>
          </tr>
          
          <!-- 第2行以降: 階層的な性能ヘッダー -->
          <tr v-for="level in maxPerformanceLevel" :key="`level-${level}`">
            <!-- ステークホルダーヘッダー（最初の行のみ） -->
            <template v-if="level === 1">
              <th 
                v-for="stakeholder in stakeholders" 
                :key="stakeholder.id"
                :rowspan="maxPerformanceLevel"
                class="stakeholder-header"
              >
                <div class="stakeholder-header-content">
                  <div class="stakeholder-name-vertical">{{ stakeholder.name }}</div>
                  <div class="stakeholder-votes-horizontal">{{ stakeholder.votes }}票</div>
                </div>
              </th>
            </template>
            
            <!-- 性能ヘッダー（各レベル） -->
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

        <!-- ボディ: ニーズ行 -->
        <tbody>
          <tr v-for="need in needs" :key="need.id">
            <!-- ニーズ名 -->
            <td class="need-header">
              <div class="need-info">
                {{ need.name }}
                <span v-if="need.category" class="category-tag">
                  {{ need.category }}
                </span>
              </div>
            </td>

            <!-- ステークホルダー×ニーズセル -->
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

            <!-- 合計票数セル -->
            <td class="matrix-cell total-votes-cell">
              <div class="cell-content total-votes-value">
                {{ getTotalVotesForNeed(need.id).toFixed(1) }}
              </div>
            </td>

            <!-- 性能×ニーズセル（末端のみクリック可能） -->
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
                  <!-- 効用関数ボタン -->
                  <button
                    v-if="getUtilityButtonType(need.id, perf.id) !== 'none'"
                    class="utility-button"
                    :class="`utility-button-${getUtilityButtonType(need.id, perf.id)}`"
                    @click="openUtilityModal(need.id, perf.id, $event)"
                    :title="getUtilityButtonType(need.id, perf.id) === 'warning' ? '効用関数の確認が必要です' : '効用関数を設定'"
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

          <!-- 集計行: ↑票数 -->
          <tr class="summary-row">
            <td :colspan="stakeholders.length + 1" class="summary-empty"></td>
            <td class="summary-label-cell">↑票数</td>
            <td
              v-for="perf in getAllPerformanceColumns()"
              :key="`up-${perf.id}`"
              class="summary-cell"
            >
              <span v-if="perf.is_leaf" class="summary-value">{{ getUpVotesForPerformance(perf.id).toFixed(1) }}</span>
            </td>
          </tr>

          <!-- 集計行: ↓票数 -->
          <tr class="summary-row">
            <td :colspan="stakeholders.length + 1" class="summary-empty"></td>
            <td class="summary-label-cell">↓票数</td>
            <td
              v-for="perf in getAllPerformanceColumns()"
              :key="`down-${perf.id}`"
              class="summary-cell"
            >
              <span v-if="perf.is_leaf" class="summary-value">{{ getDownVotesForPerformance(perf.id).toFixed(1) }}</span>
            </td>
          </tr>

          <!-- 集計行: 有効投票数 -->
          <tr class="summary-row effective-votes-row">
            <td :colspan="stakeholders.length + 1" class="summary-empty effective-votes-empty"></td>
            <td class="summary-label-cell effective-votes-label">有効投票数</td>
            <td
              v-for="perf in getAllPerformanceColumns()"
              :key="`effective-${perf.id}`"
              class="summary-cell effective-votes-cell"
            >
              <span v-if="perf.is_leaf" class="summary-value">{{ getEffectiveVotesForPerformance(perf.id).toFixed(1) }}</span>
            </td>
          </tr>

          <!-- 集計行: 大項目ごとの有効投票数 -->
          <tr class="summary-row root-summary-row">
            <td :colspan="stakeholders.length + 1" class="summary-empty root-summary-empty"></td>
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

          <!-- 集計行: p値 (有効投票数 / V) -->
          <tr class="summary-row p-value-row">
            <td :colspan="stakeholders.length + 1" class="summary-empty p-value-empty"></td>
            <td class="summary-label-cell p-value-label">p= Σv_i / V</td>
            <td
              v-for="perf in getAllPerformanceColumns()"
              :key="`p-${perf.id}`"
              class="summary-cell p-value-cell"
            >
              <span v-if="perf.is_leaf" class="summary-value">{{ getPValueForPerformance(perf.id).toFixed(3) }}</span>
            </td>
          </tr>

          <!-- 集計行: p² -->
          <tr class="summary-row p-squared-row">
            <td :colspan="stakeholders.length + 1" class="summary-empty p-squared-empty"></td>
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

          <!-- 集計行: HHI (大項目ごとのΣp²) -->
          <tr class="summary-row hhi-row">
            <td :colspan="stakeholders.length + 1" class="summary-empty hhi-empty"></td>
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

    <!-- 分解不足の性能分析（マトリクスの外） -->
    <DecompositionAnalysis
      :analysis="insufficientDecompositionAnalysis"
      :needsCount="needs.length"
      :hasStakeholdersOrPerformances="stakeholders.length > 0 || performances.length > 0"
      @navigate-to-performance="navigateToPerformanceManagement"
    />

    <!-- 効用関数設定モーダル -->
    <div v-if="showUtilityModal && currentUtilityEdit" class="modal-overlay" @click="closeUtilityModal">
      <div class="modal-content utility-modal" @click.stop>
        <h3>効用関数設定</h3>
        
        <div class="modal-info">
          <div class="info-row">
            <strong>性能:</strong>
            <span>{{ performances.find(p => p.id === currentUtilityEdit!.performanceId)?.name }}</span>
          </div>
          <div class="info-row">
            <strong>ニーズ:</strong>
            <span>{{ needs.find(n => n.id === currentUtilityEdit!.needId)?.name }}</span>
          </div>
          <div class="info-row">
            <strong>方向:</strong>
            <span class="direction-badge">
              {{ getPerformanceRelationSymbol(currentUtilityEdit!.needId, currentUtilityEdit!.performanceId) }}
              {{ getPerformanceRelation(currentUtilityEdit!.needId, currentUtilityEdit!.performanceId)?.direction === 'up' ? '向上' : '抑制' }}
            </span>
          </div>
        </div>

        <div class="graph-section">
          <div class="graph-container">
            <!-- インフォと設定ボタン -->
            <div class="graph-controls">
              <!-- インポートボタン: 常に表示 -->
              <button 
                class="graph-control-button import-button" 
                @click.stop="handleImportExcel"
                title="Excelから効用関数をインポート"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                  <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/>
                </svg>
              </button>
              <!-- カメラボタン: 効用関数が登録されている場合のみ表示 -->
              <button 
                v-if="hasUtilityFunction()"
                class="graph-control-button camera-button" 
                @click.stop="handleDownloadGraph"
                title="グラフを画像でダウンロード"
              >
                <FontAwesomeIcon :icon="['fas', 'camera']" />
              </button>
              <!-- エクセルボタン: 効用関数が登録されている場合のみ表示 -->
              <button 
                v-if="hasUtilityFunction()"
                class="graph-control-button excel-button" 
                @click.stop="handleDownloadExcel"
                title="効用関数をExcelでダウンロード"
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
              <!-- コピーボタン: 効用関数が登録されている場合のみ表示 -->
              <button 
                v-if="hasUtilityFunction()"
                class="graph-control-button copy-button" 
                @click.stop="handleCopyUtilityFunction"
                title="効用関数をコピー"
              >
                <FontAwesomeIcon :icon="['fas', 'copy']" />
              </button>
              <!-- ペーストボタン: 同じ性能にコピーしたデータがある場合のみ表示 -->
              <button 
                v-if="canPasteUtilityFunction()"
                class="graph-control-button paste-button" 
                @click.stop="handlePasteUtilityFunction"
                title="効用関数を貼り付け"
              >
                <FontAwesomeIcon :icon="['fas', 'paste']" />
              </button>
              <button 
                class="graph-control-button info-button" 
                @click.stop="toggleInfoPopup"
                title="使い方"
              >
                <FontAwesomeIcon :icon="['fas', 'info-circle']" />
              </button>
              <button 
                class="graph-control-button settings-button" 
                @click.stop="toggleSettingsPopup"
                title="設定"
              >
                <FontAwesomeIcon :icon="['fas', 'gear']" />
              </button>
              
              <!-- インフォポップアップ -->
              <div v-if="showInfoPopup" class="graph-popup info-popup" @click.stop>
                <div class="popup-header">
                  <h4>グラフの使い方</h4>
                  <button class="popup-close" @click="showInfoPopup = false">×</button>
                </div>
                <div class="popup-content">
                  <p class="info-section-title">【連続関数】</p>
                  <ul class="info-list">
                    <li><strong>点をプロット:</strong> グラフ内をクリック</li>
                    <li><strong>点を削除:</strong> プロットした点をクリック</li>
                    <li><strong>線の表示:</strong> 2点以上で自動的に結ばれます</li>
                    <li><strong>座標確認:</strong> 点にマウスオーバー</li>
                    <li><strong>軸範囲:</strong> 下のスライダーで調整可能</li>
                  </ul>
                  <p class="info-section-title">【離散関数】</p>
                  <ul class="info-list">
                    <li><strong>点をプロット:</strong> グラフ内クリックで最寄りの点の効用値を更新</li>
                    <li><strong>点を削除:</strong> 緑の点をクリック（またはマトリクスで行削除）</li>
                    <li><strong>座標確認:</strong> 点にマウスオーバー</li>
                  </ul>
                  <p class="info-section-title">【コピー&ペースト】</p>
                  <ul class="info-list">
                    <li><strong>コピー:</strong> 効用関数が登録されている場合、<FontAwesomeIcon :icon="['fas', 'copy']" />ボタンが表示されます</li>
                    <li><strong>ペースト:</strong> 同じ性能の別のニーズにのみ貼り付け可能です</li>
                  </ul>
                </div>
              </div>
              
              <!-- 設定ポップアップ -->
              <div v-if="showSettingsPopup" class="graph-popup settings-popup" @click.stop>
                <div class="popup-header">
                  <h4>線の補完設定</h4>
                  <button class="popup-close" @click="showSettingsPopup = false">×</button>
                </div>
                <div class="popup-content">
                  <div class="setting-item">
                    <label class="setting-label">補完方法 (連続関数のみ):</label>
                    <select v-model="interpolationType" class="setting-select" :disabled="currentUtilityEdit?.type === 'discrete'">
                      <option value="linear">線形補完</option>
                      <option value="step">ステップ補完</option>
                      <option value="smooth">スムーズ補完</option>
                    </select>
                  </div>
                  <div class="setting-description">
                    <template v-if="currentUtilityEdit?.type === 'discrete'">
                      ⚠️ 離散関数では線は表示されません。各離散値は独立した点として表示されます。
                    </template>
                    <template v-else-if="interpolationType === 'linear'">
                      点と点を直線で結びます（デフォルト）
                    </template>
                    <template v-else-if="interpolationType === 'step'">
                      階段状に補完します（段階的な変化）
                    </template>
                    <template v-else-if="interpolationType === 'smooth'">
                      曲線で滑らかに補完します
                    </template>
                  </div>
                </div>
              </div>
            </div>
            
            <svg class="utility-graph" viewBox="0 0 420 330" preserveAspectRatio="xMidYMid meet" @click="handleGraphClick">
              <!-- 背景 -->
              <rect x="50" y="20" width="330" height="260" fill="#f8f9fa" stroke="#dee2e6" stroke-width="1"/>
              
              <!-- グリッド線（縦） -->
              <line v-for="i in 10" :key="`v-${i}`" 
                :x1="50 + i * 33" :y1="20" 
                :x2="50 + i * 33" :y2="280" 
                stroke="#e9ecef" stroke-width="1"/>
              
              <!-- グリッド線（横） -->
              <line v-for="i in 10" :key="`h-${i}`" 
                :x1="50" :y1="20 + i * 26" 
                :x2="380" :y2="20 + i * 26" 
                stroke="#e9ecef" stroke-width="1"/>
              
              <!-- 基準線: y=0.5 (黄色) -->
              <line x1="50" :y1="20 + 260 * 0.5" x2="380" :y2="20 + 260 * 0.5" 
                stroke="#fbbf24" stroke-width="2" stroke-dasharray="5,5" opacity="0.7"/>
              
              <!-- 基準線: y=0.8 (赤) -->
              <line x1="50" :y1="20 + 260 * 0.2" x2="380" :y2="20 + 260 * 0.2" 
                stroke="#ef4444" stroke-width="2" stroke-dasharray="5,5" opacity="0.7"/>
              
              <!-- Y軸 -->
              <line x1="50" y1="20" x2="50" y2="280" stroke="#495057" stroke-width="2"/>
              
              <!-- X軸 -->
              <line x1="50" y1="280" x2="380" y2="280" stroke="#495057" stroke-width="2"/>
              
              <!-- プロットされた点（連続関数） -->
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
              
              <!-- プロットされた点（離散関数） -->
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
              
              <!-- カスタムツールチップ -->
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
              
              <!-- プロット点を結ぶ線（連続関数） -->
              <polyline 
                v-if="currentUtilityEdit?.type === 'continuous' && utilityPoints.length > 1 && interpolationType !== 'smooth'"
                :points="getPolylinePoints()"
                fill="none"
                stroke="#3b82f6"
                stroke-width="2"
                opacity="0.6"
                :key="`polyline-${utilityPoints.length}-${interpolationType}`"
              />
              
              <!-- スムーズ補完用のパス（連続関数） -->
              <path
                v-if="currentUtilityEdit?.type === 'continuous' && utilityPoints.length > 1 && interpolationType === 'smooth'"
                :d="getSmoothPath()"
                fill="none"
                stroke="#3b82f6"
                stroke-width="2"
                opacity="0.6"
                :key="`path-${utilityPoints.length}-${interpolationType}`"
              />
              
              <!-- Y軸ラベル -->
              <text x="25" y="25" font-size="12" fill="#495057" font-weight="600">1.0</text>
              <text x="25" y="153" font-size="12" fill="#495057" font-weight="600">0.5</text>
              <text x="25" y="283" font-size="12" fill="#495057" font-weight="600">0.0</text>
              
              <!-- Y軸タイトル -->
              <text x="15" y="150" font-size="14" fill="#495057" font-weight="600" 
                transform="rotate(-90, 15, 150)">効用値</text>
              
              <!-- X軸ラベル（連続関数の場合） -->
              <template v-if="currentUtilityEdit?.type === 'continuous'">
                <text x="50" y="295" font-size="11" fill="#495057" text-anchor="middle">{{ axisRange.min }}</text>
                <text x="215" y="295" font-size="11" fill="#495057" text-anchor="middle">{{ ((axisRange.min + axisRange.max) / 2).toFixed(2) }}</text>
                <text x="380" y="295" font-size="11" fill="#495057" text-anchor="middle">{{ axisRange.max }}</text>
              </template>
              
              <!-- X軸ラベル（離散関数の場合） -->
              <template v-if="currentUtilityEdit?.type === 'discrete'">
                <g v-for="(row, index) in discreteRows" :key="`label-${index}`">
                  <text 
                    :x="getDiscreteXPosition(index)" 
                    y="295" 
                    font-size="10" 
                    fill="#495057" 
                    text-anchor="middle"
                  >
                    {{ row.label || `#${index + 1}` }}
                  </text>
                </g>
              </template>
              
              <!-- X軸タイトル -->
              <text x="215" y="310" font-size="14" fill="#495057" font-weight="600" 
                text-anchor="middle">
                {{ getCurrentPerformanceUnit() ? `${performances.find(p => p.id === currentUtilityEdit!.performanceId)?.name} (${getCurrentPerformanceUnit()})` : `${performances.find(p => p.id === currentUtilityEdit!.performanceId)?.name}` }}
              </text>
              
              <!-- 基準線のラベル -->
              <text x="385" :y="20 + 260 * 0.5 + 5" font-size="11" fill="#f59e0b" font-weight="600">0.5</text>
              <text x="385" :y="20 + 260 * 0.2 + 5" font-size="11" fill="#dc2626" font-weight="600">0.8</text>
            </svg>
          </div>
          
          <!-- タイプ切り替え -->
          <div class="type-switcher">
            <span class="type-label">タイプ:</span>
            <button 
              class="type-button" 
              :class="{ active: currentUtilityEdit?.type === 'continuous' }"
              @click="switchToType('continuous')"
            >
              <span class="type-icon">{{ currentUtilityEdit?.type === 'continuous' ? '●' : '○' }}</span>
              連続
            </button>
            <button 
              class="type-button" 
              :class="{ active: currentUtilityEdit?.type === 'discrete' }"
              @click="switchToType('discrete')"
            >
              <span class="type-icon">{{ currentUtilityEdit?.type === 'discrete' ? '●' : '○' }}</span>
              離散
            </button>
          </div>
          
          <!-- 横軸範囲設定（連続関数の場合のみ） -->
          <div v-if="currentUtilityEdit?.type === 'continuous'" class="axis-range-control">
            <div class="range-header">
              <span class="range-label">横軸範囲:</span>
              <span class="range-tip">0付近は細かく調整可能</span>
            </div>
            
            <div class="range-single-row">
              <input 
                type="number" 
                v-model.number="axisRange.min" 
                @input="updateRangeFromInput"
                step="any"
                class="range-input"
                placeholder="下限"
              />
              
              <div ref="rangeSliderElement" class="nouislider-container"></div>
              
              <input 
                type="number" 
                v-model.number="axisRange.max" 
                @input="updateRangeFromInput"
                step="any"
                class="range-input"
                placeholder="上限"
              />
            </div>
          </div>
          
          <!-- 離散関数用のマトリクス入力 -->
          <div v-if="currentUtilityEdit?.type === 'discrete'" class="discrete-matrix-control">
            <div class="matrix-header">
              <span class="matrix-label">離散値マトリクス:</span>
              <button class="add-row-button" @click="addDiscreteRow">
                ＋ 行を追加
              </button>
            </div>
            
            <div class="discrete-matrix">
              <table class="discrete-table">
                <thead>
                  <tr>
                    <th class="label-column">性能値ラベル</th>
                    <th class="value-column">効用値 (0-1)</th>
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
                        placeholder="例: 小さい"
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
              💡 効用値は手入力せず、上のグラフで点をプロットすることでも設定できます
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button 
            v-if="getUtilityButtonType(currentUtilityEdit!.needId, currentUtilityEdit!.performanceId) === 'check' || getUtilityButtonType(currentUtilityEdit!.needId, currentUtilityEdit!.performanceId) === 'warning'"
            class="danger" 
            @click="resetUtilityFunction"
          >
            初期化
          </button>
          <div class="spacer"></div>
          <button class="secondary" @click="closeUtilityModal">
            保存せずに終了
          </button>
          <button class="primary" @click="saveUtilityFunction">
            保存
          </button>
        </div>
      </div>
    </div>

    <!-- 空状態 -->
    <div v-else-if="!(needs.length > 0 && (stakeholders.length > 0 || performances.length > 0))" class="empty-matrix">
      <p>ステークホルダー、ニーズ、性能を登録してください</p>
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

// 効用関数データ構造
interface UtilityFunction {
  need_id: string
  performance_id: string
  direction: 'up' | 'down'
  type: 'continuous' | 'discrete' // 連続 or 離散
  axisMin?: number // 横軸の下限（連続関数用）
  axisMax?: number // 横軸の上限（連続関数用）
  points?: UtilityPoint[] // プロットされた点
  discreteRows?: DiscreteRow[] // 離散関数のマトリクスデータ
  saved: boolean // 保存済みフラグ
  warning: boolean // 警告状態フラグ
  archived: boolean // アーカイブ状態フラグ
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

// 効用関数のローカルストレージ
const utilityFunctions = ref<UtilityFunction[]>([])

// ポップアップ表示状態
const showUtilityModal = ref(false)
const currentUtilityEdit = ref<{
  needId: string
  performanceId: string
  type: 'continuous' | 'discrete'
} | null>(null)

// 横軸範囲の設定（連続関数用）
const axisRange = ref({
  min: 0,
  max: 100
})

// noUiSlider用のref
const rangeSliderElement = ref<HTMLElement | null>(null)
let rangeSliderInstance: any = null

// プロットされた点のデータ構造
interface UtilityPoint {
  x: number // SVG座標
  y: number // SVG座標
  valueX: number // 実際のX値（性能値）
  valueY: number // 実際のY値（効用値 0-1）
}

// 現在編集中の効用関数の点
const utilityPoints = ref<UtilityPoint[]>([])

// 離散関数用のデータ構造
interface DiscreteRow {
  label: string // 性能値のラベル（例: 「小さい」）
  value: number // 効用値 (0-1)
}

// 離散関数の行データ
const discreteRows = ref<DiscreteRow[]>([
  { label: '', value: 0 }
])

// 離散関数の行を追加
function addDiscreteRow() {
  discreteRows.value.push({ label: '', value: 0 })
}

// 離散関数の行を削除
function removeDiscreteRow(index: number) {
  if (discreteRows.value.length > 1) {
    discreteRows.value.splice(index, 1)
  }
}

// ポップアップ表示状態
const showInfoPopup = ref(false)
const showSettingsPopup = ref(false)

// 線の補完タイプ
const interpolationType = ref<'linear' | 'step' | 'smooth'>('linear')

// コピーした効用関数データ
const copiedUtilityFunction = ref<{
  performanceId: string
  type: 'continuous' | 'discrete'
  points: Array<{ x: number; y: number; valueX: number; valueY: number }>
  discreteMapping: Array<{ label: string; value: number }>
  axisRange: { min: number; max: number }
  interpolationType: 'linear' | 'step' | 'smooth'
} | null>(null)

// ツールチップ表示用
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

// ポップアップトグル関数
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
  
  // 現在の効用関数データをコピー
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
  
  // SVG要素を取得
  const svgElement = document.querySelector('.utility-graph') as SVGElement
  if (!svgElement) return
  
  // SVGのクローンを作成
  const svgClone = svgElement.cloneNode(true) as SVGElement
  
  // SVGを文字列に変換
  const svgData = new XMLSerializer().serializeToString(svgClone)
  const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })
  
  // Canvasを作成してSVGを描画
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  const img = new Image()
  const url = URL.createObjectURL(svgBlob)
  
  img.onload = () => {
    // 高解像度で描画
    canvas.width = 1260 // 420 * 3
    canvas.height = 990 // 330 * 3
    
    // 白背景を描画
    ctx.fillStyle = 'white'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    
    // SVGを描画
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
    
    // PNGとしてダウンロード
    canvas.toBlob((blob) => {
      if (!blob) return
      
      const performance = performances.value.find(p => p.id === currentUtilityEdit.value!.performanceId)
      const need = needs.value.find(n => n.id === currentUtilityEdit.value!.needId)
      const filename = `効用関数_${performance?.name || 'performance'}_${need?.name || 'need'}.png`
      
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
  
  // ワークブックを作成
  const wb = XLSX.utils.book_new()
  
  // 【データシート】を作成
  if (currentUtilityEdit.value.type === 'continuous') {
    // 連続関数の場合
    const dataRows: (string | number)[][] = [
      ['連続関数データ'],
      [''],
      ['補完方法', interpolationType.value === 'linear' ? '線形' : interpolationType.value === 'step' ? 'ステップ' : 'スムーズ', '「線形」「ステップ」「スムーズ」のいずれかを入力してください'],
      ['軸範囲（最小）', axisRange.value.min, ''],
      ['軸範囲（最大）', axisRange.value.max, ''],
      [''],
      ['性能値', '効用値']
    ]
    
    // ポイントをX値でソート
    const sortedPoints = [...utilityPoints.value].sort((a, b) => a.valueX - b.valueX)
    
    sortedPoints.forEach(point => {
      dataRows.push([point.valueX, point.valueY])
    })
    
    const ws_data = XLSX.utils.aoa_to_sheet(dataRows)
    
    // 列幅を設定
    ws_data['!cols'] = [
      { wch: 20 },
      { wch: 15 },
      { wch: 40 }
    ]
    
    XLSX.utils.book_append_sheet(wb, ws_data, '連続関数データ')
  } else {
    // 離散関数の場合
    const dataRows: (string | number)[][] = [
      ['離散関数データ'],
      [''],
      ['ラベル', '効用値']
    ]
    
    discreteRows.value.forEach(row => {
      if (row.label !== '' || row.value !== 0) {
        dataRows.push([row.label, row.value])
      }
    })
    
    const ws_data = XLSX.utils.aoa_to_sheet(dataRows)
    
    // 列幅を設定
    ws_data['!cols'] = [
      { wch: 20 },
      { wch: 15 }
    ]
    
    XLSX.utils.book_append_sheet(wb, ws_data, '離散関数データ')
  }
  
  // ファイルをダウンロード
  const filename = `効用関数_${performance?.name || 'performance'}_${need?.name || 'need'}.xlsx`
  XLSX.writeFile(wb, filename)
}

function handleImportExcel() {
  // ファイル選択ダイアログを表示
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
        
        // シート名から関数タイプを判定
        let functionType: 'continuous' | 'discrete' | null = null
        
        if (workbook.Sheets['連続関数データ']) {
          functionType = 'continuous'
        } else if (workbook.Sheets['離散関数データ']) {
          functionType = 'discrete'
        } else {
          alert('エラー: 「連続関数データ」または「離散関数データ」シートが見つかりません')
          return
        }
        
        // データシートを読み込み
        if (functionType === 'continuous') {
          const dataSheet = workbook.Sheets['連続関数データ']
          if (!dataSheet) {
            alert('エラー: 「連続関数データ」シートが見つかりません')
            return
          }
          
          const dataJson = XLSX.utils.sheet_to_json(dataSheet, { header: 1 }) as any[][]
          
          // 補完方法を取得（B3セル = インデックス[2][1]）
          const interpolationValue = dataJson[2]?.[1]
          
          let newInterpolationType: 'linear' | 'step' | 'smooth' = 'linear'
          if (typeof interpolationValue === 'string') {
            const normalizedValue = interpolationValue.trim()
            if (normalizedValue === '線形' || normalizedValue === 'linear') {
              newInterpolationType = 'linear'
            } else if (normalizedValue === 'ステップ' || normalizedValue === 'step') {
              newInterpolationType = 'step'
            } else if (normalizedValue === 'スムーズ' || normalizedValue === 'smooth') {
              newInterpolationType = 'smooth'
            }
          }
          
          
          // 軸範囲を取得
          const minValue = Number(dataJson[3]?.[1])
          const maxValue = Number(dataJson[4]?.[1])
          
          // データポイントを取得（8行目以降 = インデックス7以降）
          // ヘッダー行「性能値, 効用値」をスキップ
          const points: Array<{ x: number; y: number; valueX: number; valueY: number }> = []
          for (let i = 7; i < dataJson.length; i++) {
            const row = dataJson[i]
            if (row && row[0] !== undefined && row[1] !== undefined) {
              const valueX = Number(row[0])
              const valueY = Number(row[1])
              
              // 数値であることを確認（ヘッダー行を除外）
              if (!isNaN(valueX) && !isNaN(valueY)) {
                // SVG座標に変換
                const x = 50 + ((valueX - minValue) / (maxValue - minValue)) * 330
                const y = 20 + (1 - valueY) * 260
                
                points.push({ x, y, valueX, valueY })
              }
            }
          }
          
          // データを適用（順序が重要）
          currentUtilityEdit.value!.type = 'continuous'
          axisRange.value = { min: minValue, max: maxValue }
          interpolationType.value = newInterpolationType
          utilityPoints.value = points
          
          
          // 次のティックでスライダーを再初期化し、グラフを強制再描画
          nextTick(() => {
            initRangeSlider()
            // 強制的に再描画をトリガー
            if (utilityPoints.value.length > 0) {
              const temp = [...utilityPoints.value]
              utilityPoints.value = temp
            }
          })
          
          alert(`連続関数データをインポートしました（補完方法: ${newInterpolationType === 'linear' ? '線形' : newInterpolationType === 'step' ? 'ステップ' : 'スムーズ'}）`)
        } else {
          const dataSheet = workbook.Sheets['離散関数データ']
          if (!dataSheet) {
            alert('エラー: 「離散関数データ」シートが見つかりません')
            return
          }
          
          const dataJson = XLSX.utils.sheet_to_json(dataSheet, { header: 1 }) as any[][]
          
          // データポイントを取得（4行目以降 = インデックス3以降）
          // ヘッダー行「ラベル, 効用値」をスキップ
          const rows: Array<{ label: string; value: number }> = []
          for (let i = 3; i < dataJson.length; i++) {
            const row = dataJson[i]
            if (row && row[0] !== undefined && row[1] !== undefined) {
              const value = Number(row[1])
              // 効用値が数値であることを確認（ヘッダー行を除外）
              if (!isNaN(value)) {
                rows.push({
                  label: String(row[0]),
                  value: value
                })
              }
            }
          }
          
          // データを適用
          currentUtilityEdit.value!.type = 'discrete'
          discreteRows.value = rows.length > 0 ? rows : [{ label: '', value: 0 }]
          
          alert('離散関数データをインポートしました')
        }
        
      } catch (error) {
        console.error('Excel読み込みエラー:', error)
        alert('エラー: Excelファイルの読み込みに失敗しました')
      }
    }
    
    reader.readAsArrayBuffer(file)
  }
  
  input.click()
}

// テンプレートファイルをダウンロード
function downloadTemplateFile() {
  // ワークブックを作成
  const wb = XLSX.utils.book_new()
  
  // 【説明シート】を作成
  const instructionsData: (string | number)[][] = [
    ['効用関数テンプレートファイル'],
    [''],
    ['このファイルは、効用関数データをインポートするためのテンプレートです。'],
    ['以下の手順で使用してください：'],
    [''],
    ['【使い方】'],
    ['1. 効用関数設定モーダルを開く（マトリクスの性能×ニーズセルで効用関数ボタンをクリック）'],
    ['2. モーダルで「インポート」ボタンをクリック'],
    ['3. 使用したいシート（「連続関数データ」または「離散関数データ」）を編集'],
    ['4. このファイルを選択してアップロード'],
    [''],
    ['【注意事項】'],
    ['・インポートするデータの種類（連続/離散）は、使用するシート名で自動判定されます'],
    ['・「連続関数データ」シートを使う場合: 連続関数としてインポートされます'],
    ['・「離散関数データ」シートを使う場合: 離散関数としてインポートされます'],
    ['・連続関数の補完方法は「線形」「ステップ」「スムーズ」のいずれかで入力してください'],
    ['・シート名は変更しないでください'],
    ['・両方のシートがある場合、連続関数データが優先されます'],
  ]
  
  const ws_instructions = XLSX.utils.aoa_to_sheet(instructionsData)
  ws_instructions['!cols'] = [{ wch: 90 }]
  XLSX.utils.book_append_sheet(wb, ws_instructions, '説明')
  
  // 【連続関数データシート（見本）】を作成
  const continuousData: (string | number)[][] = [
    ['連続関数データ'],
    [''],
    ['補完方法', '線形', '「線形」「ステップ」「スムーズ」のいずれかを入力してください'],
    ['軸範囲（最小）', 0, '性能値の最小値を入力'],
    ['軸範囲（最大）', 100, '性能値の最大値を入力'],
    [''],
    ['性能値', '効用値'],
    [0, 0],
    [25, 0.3],
    [50, 0.6],
    [75, 0.85],
    [100, 1.0],
    [''],
    ['※ 上記は見本データです。実際のデータに置き換えてください。'],
    ['※ 性能値と効用値は数値で入力してください。'],
    ['※ 効用値は0〜1の範囲で入力してください。'],
  ]
  
  const ws_continuous = XLSX.utils.aoa_to_sheet(continuousData)
  ws_continuous['!cols'] = [{ wch: 20 }, { wch: 15 }, { wch: 50 }]
  
  XLSX.utils.book_append_sheet(wb, ws_continuous, '連続関数データ')
  
  // 【離散関数データシート（見本）】を作成
  const discreteData: (string | number)[][] = [
    ['離散関数データ'],
    [''],
    ['ラベル', '効用値'],
    ['とても小さい', 0.2],
    ['小さい', 0.4],
    ['普通', 0.6],
    ['大きい', 0.8],
    ['とても大きい', 1.0],
    [''],
    ['※ 上記は見本データです。実際のデータに置き換えてください。'],
    ['※ ラベルは任意の文字列、効用値は0〜1の範囲の数値で入力してください。'],
  ]
  
  const ws_discrete = XLSX.utils.aoa_to_sheet(discreteData)
  ws_discrete['!cols'] = [{ wch: 20 }, { wch: 15 }]
  XLSX.utils.book_append_sheet(wb, ws_discrete, '離散関数データ')
  
  // ファイルをダウンロード
  const filename = '効用関数テンプレート.xlsx'
  XLSX.writeFile(wb, filename)
}

// マトリクスを画像としてダウンロード（縦書き対応版）
async function downloadMatrixAsImageVertical() {
  try {
    const button = document.querySelector('.matrix-image-button span')
    if (button) {
      button.textContent = '画像生成中...'
    }
    
    // 複数の候補からテーブル要素を取得
    let targetElement: HTMLElement | null = null
    
    // 候補1: matrix-table を直接取得
    const matrixTable = document.querySelector('.matrix-table') as HTMLElement
    if (matrixTable && matrixTable.offsetWidth > 0) {
      targetElement = matrixTable
    }
    
    // 候補2: matrix-container を取得
    if (!targetElement) {
      const matrixContainer = document.querySelector('.matrix-container') as HTMLElement
      if (matrixContainer && matrixContainer.offsetWidth > 0) {
        targetElement = matrixContainer
      }
    }
    
    // 候補3: table要素を直接取得
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
      alert('マトリクステーブルが見つかりません')
      if (button) button.textContent = 'マトリクスを画像ダウンロード'
      return
    }
    
    // 縦書き要素を取得して一時的に非表示にする
    const verticalElements = targetElement.querySelectorAll('.performance-header')
    const originalVisibility: { element: HTMLElement; visibility: string; color: string }[] = []

    verticalElements.forEach(el => {
      const htmlEl = el as HTMLElement
      const computedStyle = window.getComputedStyle(htmlEl)
      originalVisibility.push({
        element: htmlEl,
        visibility: computedStyle.visibility,
        color: computedStyle.color
      })
      // テキストを透明にする（レイアウトは保持）
      htmlEl.style.color = 'transparent'
    })
    
    // html2canvasで画像化（縦書きテキストは透明）
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
    
    // スタイルを元に戻す
    originalVisibility.forEach(({ element, visibility, color }) => {
      element.style.visibility = visibility
      element.style.color = color
    })
    
    
    if (baseCanvas.width === 0 || baseCanvas.height === 0) {
      alert('画像生成に失敗しました（サイズが0です）')
      if (button) button.textContent = 'マトリクスを画像ダウンロード'
      return
    }
    
    // 新しいキャンバスを作成して縦書きテキストを描画
    const finalCanvas = document.createElement('canvas')
    finalCanvas.width = baseCanvas.width
    finalCanvas.height = baseCanvas.height
    const ctx = finalCanvas.getContext('2d')
    
    if (!ctx) {
      alert('キャンバスコンテキストの取得に失敗しました')
      if (button) button.textContent = 'マトリクスを画像ダウンロード'
      return
    }
    
    // ベース画像を描画
    ctx.drawImage(baseCanvas, 0, 0)
    
    // 性能ヘッダーのテキストを縦書きで再描画
    const tableRect = targetElement.getBoundingClientRect()
    const scrollLeft = targetElement.scrollLeft || 0
    const scrollTop = targetElement.scrollTop || 0
    
    verticalElements.forEach(el => {
      const htmlEl = el as HTMLElement
      const rect = htmlEl.getBoundingClientRect()
      const computedStyle = window.getComputedStyle(htmlEl)
      
      // テーブル内の相対位置を計算（scale考慮、スクロール補正）
      const x = (rect.left - tableRect.left + scrollLeft) * 2
      const y = (rect.top - tableRect.top + scrollTop) * 2
      const width = rect.width * 2
      const height = rect.height * 2
      
      
      // 元の背景色を取得して描画
      const bgColor = computedStyle.backgroundColor
      ctx.fillStyle = bgColor
      ctx.fillRect(x, y, width, height)
      
      // セルの境界線を再描画（通常の境界線）
      ctx.strokeStyle = '#dee2e6'
      ctx.lineWidth = 1
      ctx.strokeRect(x, y, width, height)
      
      // 末端性能（is-leaf）の場合は太い色付き境界線を追加
      if (htmlEl.classList.contains('is-leaf')) {
        const borderColor = computedStyle.borderTopColor || computedStyle.borderColor
        ctx.strokeStyle = borderColor
        ctx.lineWidth = 4
        ctx.strokeRect(x + 2, y + 2, width - 4, height - 4)
      }
      
      // 縦書きテキストを描画
      const text = htmlEl.textContent?.trim() || ''
      if (text) {
        drawVerticalText(ctx, text, x, y, width, height)
      }
    })
    
    
    // ダウンロード
    finalCanvas.toBlob((blob: Blob | null) => {
      if (!blob) {
        alert('画像データの作成に失敗しました')
        return
      }
      
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `統合マトリクス_${new Date().toISOString().slice(0, 10)}.png`
      link.click()
      URL.revokeObjectURL(url)
      
    }, 'image/png', 0.95)
    
    if (button) {
      button.textContent = 'マトリクスを画像ダウンロード'
    }
    
  } catch (error) {
    console.error('画像生成エラー:', error)
    alert(`画像の生成に失敗しました: ${error}`)
    
    const button = document.querySelector('.matrix-image-button span')
    if (button) {
      button.textContent = 'マトリクスを画像ダウンロード'
    }
  }
}

// 縦書きテキストを描画するヘルパー関数
function drawVerticalText(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  width: number,
  height: number
) {
  // セルのサイズに応じてフォントサイズを調整
  const maxFontSize = 28
  const minFontSize = 16
  const size = Math.max(minFontSize, Math.min(maxFontSize, width * 0.6))
  const kerning = 0.7 // 文字間隔
  
  // サブキャンバスを作成
  const subCanvas = document.createElement('canvas')
  const subCtx = subCanvas.getContext('2d')
  if (!subCtx) return
  
  // テキストの実際の高さを計算
  const textHeight = size * kerning * text.length + (size * (1 - kerning))
  
  // テキストをセル内に中央配置
  const startX = x + (width - size) / 2
  const startY = y + Math.max(8, (height - textHeight) / 2)
  
  ;[...text].forEach((char, i) => {
    subCanvas.width = subCanvas.height = size * 2
    subCtx.clearRect(0, 0, subCanvas.width, subCanvas.height)
    subCtx.textAlign = 'center'
    subCtx.textBaseline = 'middle'
    subCtx.font = `bold ${size}px sans-serif`
    subCtx.fillStyle = '#495057'
    
    // 「ー」は90度回転
    if (char === 'ー') {
      subCtx.translate(size, size)
      subCtx.rotate(90 * Math.PI / 180)
      subCtx.translate(-size, -size)
    }
    
    subCtx.fillText(char, size, size)
    
    // 回転を戻す
    if (char === 'ー') {
      subCtx.translate(size, size)
      subCtx.rotate(-90 * Math.PI / 180)
      subCtx.translate(-size, -size)
    }
    
    // メインキャンバスに描画
    ctx.drawImage(subCanvas, startX, startY + size * kerning * i, size, size)
  })
}

// マトリクスをExcelとしてダウンロード
function downloadMatrixAsExcel() {
  // ワークブックを作成
  const wb = XLSX.utils.book_new()
  
  // マトリクスデータを配列に変換
  const matrixData: (string | number)[][] = []
  
  // 階層的な性能ヘッダーを作成
  const perfColumns = getAllPerformanceColumns()
  
  // 第1行: グループヘッダー
  const headerRow1: (string | number)[] = ['ニーズ']
  stakeholders.value.forEach(() => headerRow1.push(''))
  headerRow1.push('合計票数')
  perfColumns.forEach(() => headerRow1.push(''))
  matrixData.push(headerRow1)
  
  // 第2行以降: 階層的な性能ヘッダー（マトリクスと同じ構造）
  for (let level = 1; level <= maxPerformanceLevel.value; level++) {
    const levelRow: (string | number)[] = []
    
    // 最初の列（ニーズ列）とステークホルダー列は空
    if (level === 1) {
      levelRow.push('') // ニーズ列
      stakeholders.value.forEach(sh => levelRow.push(`${sh.name} (${sh.votes}票)`))
      levelRow.push('') // 合計票数列
    } else {
      levelRow.push('')
      stakeholders.value.forEach(() => levelRow.push(''))
      levelRow.push('')
    }
    
    // 性能の階層ヘッダー
    const cellsAtLevel = getMatrixCellsAtLevel(level)
    cellsAtLevel.forEach(cell => {
      const displayName = cell.performance.unit 
        ? `${cell.performance.name} (${cell.performance.unit})` 
        : cell.performance.name
      levelRow.push(displayName)
      
      // colspanがある場合は空セルを追加
      for (let i = 1; i < cell.colspan; i++) {
        levelRow.push('')
      }
    })
    
    matrixData.push(levelRow)
  }
  
  // データ行: 各ニーズ
  needs.value.forEach(need => {
    const row: (string | number)[] = [need.name]
    
    // ステークホルダー×ニーズ
    stakeholders.value.forEach(sh => {
      const votes = getStakeholderVotesForNeed(sh.id, need.id)
      row.push(hasStakeholderRelation(sh.id, need.id) ? votes.toFixed(1) : '')
    })
    
    // 合計票数
    row.push(getTotalVotesForNeed(need.id).toFixed(1))
    
    // 性能×ニーズ
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
  
  // 集計行: ↑票数
  const upVotesRow: (string | number)[] = ['↑票数']
  stakeholders.value.forEach(() => upVotesRow.push(''))
  upVotesRow.push('')
  perfColumns.forEach(perf => {
    upVotesRow.push(perf.is_leaf ? getUpVotesForPerformance(perf.id).toFixed(1) : '')
  })
  matrixData.push(upVotesRow)
  
  // 集計行: ↓票数
  const downVotesRow: (string | number)[] = ['↓票数']
  stakeholders.value.forEach(() => downVotesRow.push(''))
  downVotesRow.push('')
  perfColumns.forEach(perf => {
    downVotesRow.push(perf.is_leaf ? getDownVotesForPerformance(perf.id).toFixed(1) : '')
  })
  matrixData.push(downVotesRow)
  
  // 集計行: 有効投票数
  const effectiveVotesRow: (string | number)[] = ['有効投票数']
  stakeholders.value.forEach(() => effectiveVotesRow.push(''))
  effectiveVotesRow.push('')
  perfColumns.forEach(perf => {
    effectiveVotesRow.push(perf.is_leaf ? getEffectiveVotesForPerformance(perf.id).toFixed(1) : '')
  })
  matrixData.push(effectiveVotesRow)
  
  // 集計行: p値
  const pValueRow: (string | number)[] = ['p= Σv_i / V']
  stakeholders.value.forEach(() => pValueRow.push(''))
  pValueRow.push('')
  perfColumns.forEach(perf => {
    pValueRow.push(perf.is_leaf ? getPValueForPerformance(perf.id).toFixed(4) : '')
  })
  matrixData.push(pValueRow)
  
  // 集計行: p²
  const pSquaredRow: (string | number)[] = ['p²']
  stakeholders.value.forEach(() => pSquaredRow.push(''))
  pSquaredRow.push('')
  perfColumns.forEach(perf => {
    pSquaredRow.push(perf.is_leaf ? getPSquaredForPerformance(perf.id).toFixed(4) : '')
  })
  matrixData.push(pSquaredRow)
  
  // ワークシートを作成
  const ws = XLSX.utils.aoa_to_sheet(matrixData)
  
  // 列幅を自動調整
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
  
  XLSX.utils.book_append_sheet(wb, ws, '統合マトリクス')
  
  // ファイルをダウンロード
  const filename = `統合マトリクス_${new Date().toISOString().slice(0, 10)}.xlsx`
  XLSX.writeFile(wb, filename)
}


function handlePasteUtilityFunction() {
  if (!currentUtilityEdit.value || !copiedUtilityFunction.value) return
  
  // 同じ性能かチェック
  if (currentUtilityEdit.value.performanceId !== copiedUtilityFunction.value.performanceId) {
    console.warn('異なる性能には貼り付けできません')
    return
  }
  
  // コピーしたデータを貼り付け
  currentUtilityEdit.value.type = copiedUtilityFunction.value.type
  utilityPoints.value = copiedUtilityFunction.value.points.map(p => ({ ...p }))
  discreteRows.value = copiedUtilityFunction.value.discreteMapping.map(row => ({ ...row }))
  axisRange.value = { ...copiedUtilityFunction.value.axisRange }
  interpolationType.value = copiedUtilityFunction.value.interpolationType
  
  // 連続関数の場合はスライダーを再初期化
  if (currentUtilityEdit.value.type === 'continuous') {
    nextTick(() => {
      initRangeSlider()
    })
  }
  
}

// 効用関数が登録されているかチェック
function hasUtilityFunction(): boolean {
  if (!currentUtilityEdit.value) return false
  
  if (currentUtilityEdit.value.type === 'continuous') {
    return utilityPoints.value.length > 0
  } else {
    return discreteRows.value.some(row => row.label !== '' || row.value !== 0)
  }
}

// ペースト可能かチェック
function canPasteUtilityFunction(): boolean {
  if (!currentUtilityEdit.value || !copiedUtilityFunction.value) return false
  return currentUtilityEdit.value.performanceId === copiedUtilityFunction.value.performanceId
}

// グラフクリックイベントハンドラー
function handleGraphClick(event: MouseEvent) {
  const svg = event.currentTarget as SVGElement
  const rect = svg.getBoundingClientRect()
  
  // SVG座標系に変換
  const svgX = ((event.clientX - rect.left) / rect.width) * 420
  const svgY = ((event.clientY - rect.top) / rect.height) * 330
  
  // グラフエリア内かチェック（x: 50-380, y: 20-280）
  if (svgX < 50 || svgX > 380 || svgY < 20 || svgY > 280) {
    return
  }
  
  if (currentUtilityEdit.value?.type === 'continuous') {
    // 連続関数の場合
    const valueX = ((svgX - 50) / 330) * (axisRange.value.max - axisRange.value.min) + axisRange.value.min
    const valueY = 1 - ((svgY - 20) / 260) // Y軸は上が1、下が0
    
    // 点を追加（X値でソート）
    utilityPoints.value.push({
      x: svgX,
      y: svgY,
      valueX: valueX,
      valueY: Math.max(0, Math.min(1, valueY)) // 0-1にクランプ
    })
    
    // X値でソート
    utilityPoints.value.sort((a, b) => a.valueX - b.valueX)
  } else {
    // 離散関数の場合は最も近い離散値を特定
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
    
    // 効用値を更新
    const valueY = 1 - ((svgY - 20) / 260)
    discreteRows.value[closestIndex].value = Math.max(0, Math.min(1, valueY))
  }
}

// 離散関数用: インデックスからX座標を計算
function getDiscreteXPosition(index: number): number {
  if (discreteRows.value.length <= 1) {
    return 215 // 中央
  }
  const spacing = 330 / (discreteRows.value.length - 1)
  return 50 + index * spacing
}

// 離散関数の点をグラフ用に変換
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

// 点を削除
function removePoint(index: number) {
  utilityPoints.value.splice(index, 1)
}

// ツールチップ表示
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

// 離散関数用ツールチップ表示
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

// ツールチップ非表示
function hideTooltip() {
  tooltip.value.visible = false
}

// ポリラインのポイント文字列を取得
function getPolylinePoints(): string {
  if (utilityPoints.value.length < 2) return ''
  
  if (interpolationType.value === 'linear') {
    // 線形補完: 単純に点を結ぶ
    return utilityPoints.value.map(p => `${p.x},${p.y}`).join(' ')
  } else if (interpolationType.value === 'step') {
    // ステップ補完: 階段状に
    const points: string[] = []
    for (let i = 0; i < utilityPoints.value.length; i++) {
      const current = utilityPoints.value[i]
      points.push(`${current.x},${current.y}`)
      
      if (i < utilityPoints.value.length - 1) {
        const next = utilityPoints.value[i + 1]
        // 水平線を追加
        points.push(`${next.x},${current.y}`)
      }
    }
    return points.join(' ')
  } else {
    // smooth: 線形でいったん返す（後でpathに変更予定）
    return utilityPoints.value.map(p => `${p.x},${p.y}`).join(' ')
  }
}

// スムーズ補完用のパスを生成（Catmull-Rom スプライン）
function getSmoothPath(): string {
  if (utilityPoints.value.length < 2) return ''
  
  const points = utilityPoints.value
  if (points.length === 2) {
    // 2点の場合は直線
    return `M ${points[0].x},${points[0].y} L ${points[1].x},${points[1].y}`
  }
  
  // Catmull-Romスプラインで滑らかな曲線を生成
  let path = `M ${points[0].x},${points[0].y}`
  
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[Math.max(0, i - 1)]
    const p1 = points[i]
    const p2 = points[i + 1]
    const p3 = points[Math.min(points.length - 1, i + 2)]
    
    // 制御点を計算
    const cp1x = p1.x + (p2.x - p0.x) / 6
    const cp1y = p1.y + (p2.y - p0.y) / 6
    const cp2x = p2.x - (p3.x - p1.x) / 6
    const cp2y = p2.y - (p3.y - p1.y) / 6
    
    path += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${p2.x},${p2.y}`
  }
  
  return path
}

// 対数的スケールの変換関数
function sliderToValue(sliderPos: number): number {
  // sliderPos: -100 ~ 100
  const absPos = Math.abs(sliderPos)
  const sign = sliderPos >= 0 ? 1 : -1
  
  if (absPos <= 20) return sign * absPos * 0.1 // 0-20: 0.1刻み
  if (absPos <= 40) return sign * (2 + (absPos - 20)) // 21-40: 1刻み
  if (absPos <= 60) return sign * (22 + (absPos - 40) * 5) // 41-60: 5刻み
  if (absPos <= 80) return sign * (122 + (absPos - 60) * 50) // 61-80: 50刻み
  return sign * (1122 + (absPos - 80) * 500) // 81-100: 500刻み
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

// noUiSliderの初期化
function initRangeSlider() {
  if (!rangeSliderElement.value) {
    console.warn('rangeSliderElement is not available')
    return
  }
  
  // 既存のスライダーがあれば破棄
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
    
    // スライダー変更時のイベント
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

// 軸範囲が変わったときにポイントのSVG座標を更新
function updatePointCoordinates() {
  utilityPoints.value = utilityPoints.value.map(p => {
    const x = 50 + ((p.valueX - axisRange.value.min) / (axisRange.value.max - axisRange.value.min)) * 330
    const y = 20 + (1 - p.valueY) * 260
    return {
      x: Math.max(50, Math.min(380, x)), // グラフ範囲内にクランプ
      y,
      valueX: p.valueX,
      valueY: p.valueY
    }
  })
}

// 直接入力時の処理
function updateRangeFromInput() {
  // 下限が上限を超えないようにする
  if (axisRange.value.min >= axisRange.value.max) {
    axisRange.value.min = axisRange.value.max - 0.01
  }
  
  // スライダーの位置を更新
  if (rangeSliderInstance) {
    const minSliderPos = valueToSlider(axisRange.value.min)
    const maxSliderPos = valueToSlider(axisRange.value.max)
    rangeSliderInstance.set([minSliderPos, maxSliderPos])
  }
  
  // ポイントの座標も更新
  updatePointCoordinates()
}

// タイプ切り替え時の処理
function switchToType(type: 'continuous' | 'discrete') {
  if (!currentUtilityEdit.value) return
  
  currentUtilityEdit.value.type = type
  
  // 連続関数に切り替えた場合、スライダーを再初期化
  if (type === 'continuous') {
    nextTick(() => {
      initRangeSlider()
    })
  }
}

// 有効な性能IDのセット
const validPerformanceIds = computed(() => {
  return new Set(performances.value.map(p => p.id))
})

// 存在する性能への関係のみをフィルタリング
const validNeedPerformanceRelations = computed(() => {
  return needPerformanceRelations.value.filter(r => 
    validPerformanceIds.value.has(r.performance_id)
  )
})

// 最大階層レベルを計算
const maxPerformanceLevel = computed(() => {
  if (performances.value.length === 0) return 0
  return Math.max(...performances.value.map(p => p.level)) + 1
})

// チェックが1つもついていないニーズ（行）を判定
const uncheckedNeedIds = computed(() => {
  // 末端性能のIDセットを作成
  const leafPerformanceIds = new Set(
    performances.value.filter(p => p.is_leaf).map(p => p.id)
  )
  
  const checkedNeedIds = new Set<string>()
  // 末端性能への関係のみをカウント
  validNeedPerformanceRelations.value.forEach(r => {
    if (leafPerformanceIds.has(r.performance_id)) {
      checkedNeedIds.add(r.need_id)
    }
  })
  
  return new Set(needs.value.filter(n => !checkedNeedIds.has(n.id)).map(n => n.id))
})

// チェックが1つもついていない性能（列）を判定
const uncheckedPerformanceIds = computed(() => {
  // 末端性能のIDセットを作成
  const leafPerformanceIds = new Set(
    performances.value.filter(p => p.is_leaf).map(p => p.id)
  )
  
  const checkedPerformanceIds = new Set<string>()
  // 末端性能への関係のみをカウント
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

// マトリクスセル情報
interface MatrixCell {
  performance: Performance
  colspan: number
  rowspan: number
  isVisible: boolean  // このセルを表示するか（colspanで吸収される場合はfalse）
}

// マトリクス用の2次元配列を生成
const performanceMatrix = computed(() => {
  if (performances.value.length === 0) return []
  
  const maxLevel = maxPerformanceLevel.value
  const matrix: MatrixCell[][] = []
  
  // 各レベルの行を初期化
  for (let i = 0; i < maxLevel; i++) {
    matrix.push([])
  }
  
  // 末端性能の列数を計算
  function countLeafColumns(perf: Performance): number {
    if (perf.is_leaf) return 1
    const children = performances.value.filter(p => p.parent_id === perf.id)
    if (children.length === 0) return 1
    return children.reduce((sum, child) => sum + countLeafColumns(child), 0)
  }
  
  // 深さ優先探索でマトリクスを構築
  function buildMatrix(perf: Performance, level: number) {
    const leafCount = countLeafColumns(perf)
    const children = performances.value.filter(p => p.parent_id === perf.id)
    
    // 末端性能の場合は、残りの階層分rowspanを設定
    const rowspan = perf.is_leaf ? (maxLevel - level) : 1
    
    // このセルを現在の行に追加
    matrix[level].push({
      performance: perf,
      colspan: leafCount,
      rowspan: rowspan,
      isVisible: true
    })
    
    // 子要素がある場合は再帰的に処理
    if (children.length > 0) {
      children.forEach(child => buildMatrix(child, level + 1))
    }
  }
  
  // ルートレベルから開始
  const roots = performances.value.filter(p => !p.parent_id || p.parent_id === null)
  roots.forEach(root => buildMatrix(root, 0))
  
  return matrix
})

// 指定レベルのマトリクスセルを取得
function getMatrixCellsAtLevel(level: number): MatrixCell[] {
  if (level < 1 || level > performanceMatrix.value.length) return []
  return performanceMatrix.value[level - 1]
}

// 全性能を列の順番で取得（末端のみ、左から右の順序）
function getAllPerformanceColumns(): Performance[] {
  const result: Performance[] = []
  
  // 深さ優先探索で末端性能を左から右の順に収集（配列順序を保持）
  function collectLeaves(parentId: string | null | undefined) {
    // 配列順序を保持するため、filterした順序そのまま
    const children = performances.value.filter(p => p.parent_id === parentId)
    
    for (const child of children) {
      if (child.is_leaf) {
        result.push(child)
      } else {
        // 親性能の場合は子を探索
        collectLeaves(child.id)
      }
    }
  }
  
  // ルートレベルから開始
  collectLeaves(null)
  collectLeaves(undefined)
  
  return result
}

// 性能が属する大項目(ルート)のインデックスを取得
function getRootIndexForPerformance(performanceId: string): number {
  // ルート性能のリストを取得
  const roots = performances.value.filter(p => !p.parent_id || p.parent_id === null)
  
  // この性能のルートを見つける
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

// 大項目ごとのグループ情報を取得
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
    // このルートに属する末端性能をフィルタリング
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

// 大項目ごとの有効投票数を計算
function getEffectiveVotesForRoot(rootIndex: number): number {
  const group = rootGroups.value.find(g => g.rootIndex === rootIndex)
  if (!group) return 0
  
  let total = 0
  group.leafPerformances.forEach(perf => {
    total += getEffectiveVotesForPerformance(perf.id)
  })
  
  return total
}

// p値を計算: 性能の有効投票数 / 大項目の有効投票数(V)
function getPValueForPerformance(performanceId: string): number {
  const rootIndex = getRootIndexForPerformance(performanceId)
  const V = getEffectiveVotesForRoot(rootIndex)
  
  if (V === 0) return 0
  
  const effectiveVotes = getEffectiveVotesForPerformance(performanceId)
  return effectiveVotes / V
}

// p²を計算
function getPSquaredForPerformance(performanceId: string): number {
  const p = getPValueForPerformance(performanceId)
  return p * p
}

// HHI (Herfindahl-Hirschman Index) を計算: 大項目ごとのΣp²
function getHHIForRoot(rootIndex: number): number {
  const group = rootGroups.value.find(g => g.rootIndex === rootIndex)
  if (!group) return 0
  
  let sum = 0
  group.leafPerformances.forEach(perf => {
    sum += getPSquaredForPerformance(perf.id)
  })
  
  return sum
}

// p²行の全値を取得してカラースケール用の範囲を計算
const pSquaredValues = computed(() => {
  return getAllPerformanceColumns().map(perf => getPSquaredForPerformance(perf.id))
})

const pSquaredMin = computed(() => Math.min(...pSquaredValues.value.filter(v => v > 0)))
const pSquaredMax = computed(() => Math.max(...pSquaredValues.value))

// HHI行の全値を取得してカラースケール用の範囲を計算
const hhiValues = computed(() => {
  return rootGroups.value.map(group => getHHIForRoot(group.rootIndex))
})

const hhiMin = computed(() => Math.min(...hhiValues.value.filter(v => v > 0)))
const hhiMax = computed(() => Math.max(...hhiValues.value))

// V行の全値を取得してカラースケール用の範囲を計算
const vMin = computed(() => Math.min(...hhiValues.value.filter(v => v > 0)))
const vMax = computed(() => Math.max(...hhiValues.value))

// カラースケール: 淡い青から淡いピンク (p²とHHI用)
function getColorScale(value: number, min: number, max: number): string {
  if (value === 0 || max === min) return 'rgb(255, 255, 255)'
  
  const normalized = (value - min) / (max - min)
  
  // 淡い青(173, 216, 230) から 白(255, 255, 255) を経由して 淡いピンク(255, 182, 193) へ
  let r, g, b
  if (normalized > 0.5) {
    // 0.5-1.0: 白から淡いピンク
    const t = (normalized - 0.5) * 2
    r = 255
    g = Math.round(255 - 73 * t)  // 255 → 182
    b = Math.round(255 - 62 * t)  // 255 → 193
  } else {
    // 0.0-0.5: 淡い青から白
    const t = normalized * 2
    r = Math.round(173 + 82 * t)  // 173 → 255
    g = Math.round(216 + 39 * t)  // 216 → 255
    b = Math.round(230 + 25 * t)  // 230 → 255
  }
  
  return `rgb(${r}, ${g}, ${b})`
}

// カラースケール: 緑から黄を経由して赤 (V行用)
function getColorScaleGreenYellowRed(value: number, min: number, max: number): string {
  if (value === 0 || max === min) return 'rgb(255, 255, 255)'
  
  const normalized = (value - min) / (max - min)
  
  // 緑(99, 190, 123) から 黄(255, 235, 59) を経由して 赤(231, 114, 111) へ
  let r, g, b
  if (normalized > 0.5) {
    // 0.5-1.0: 黄から赤
    const t = (normalized - 0.5) * 2
    r = Math.round(255 - 24 * t)   // 255 → 231
    g = Math.round(235 - 121 * t)  // 235 → 114
    b = Math.round(59 - 52 * (1 - t) * t + 52)  // 59 → 111
  } else {
    // 0.0-0.5: 緑から黄
    const t = normalized * 2
    r = Math.round(99 + 156 * t)   // 99 → 255
    g = Math.round(190 + 45 * t)   // 190 → 235
    b = Math.round(123 - 64 * t)   // 123 → 59
  }
  
  return `rgb(${r}, ${g}, ${b})`
}

// ステークホルダー×ニーズ関係
function hasStakeholderRelation(stakeholderId: string, needId: string): boolean {
  return stakeholderNeedRelations.value.some(
    r => r.stakeholder_id === stakeholderId && r.need_id === needId
  )
}

// ステークホルダーがそのニーズに対して持つ票数を計算
function getStakeholderVotesForNeed(stakeholderId: string, needId: string): number {
  // 関係がない場合は0
  if (!hasStakeholderRelation(stakeholderId, needId)) {
    return 0
  }
  
  // このステークホルダーの総票数を取得
  const stakeholder = stakeholders.value.find(s => s.id === stakeholderId)
  if (!stakeholder) return 0
  
  // このステークホルダーが関心を持つニーズの数を計算
  const relatedNeedsCount = stakeholderNeedRelations.value.filter(
    r => r.stakeholder_id === stakeholderId
  ).length
  
  if (relatedNeedsCount === 0) return 0
  
  // 総票数を関心のあるニーズ数で按分
  return stakeholder.votes / relatedNeedsCount
}

// ニーズごとの合計票数を計算
function getTotalVotesForNeed(needId: string): number {
  let total = 0
  
  // 全ステークホルダーについて、このニーズへの票数を合計
  stakeholders.value.forEach(stakeholder => {
    total += getStakeholderVotesForNeed(stakeholder.id, needId)
  })
  
  return total
}

// ニーズに対する性能の按分票数を計算
function getPerformanceVotesForNeed(needId: string, performanceId: string): number {
  // この性能とニーズの関係がない場合は0
  const relation = getPerformanceRelation(needId, performanceId)
  if (!relation) return 0
  
  // このニーズの合計票数
  const totalVotes = getTotalVotesForNeed(needId)
  if (totalVotes === 0) return 0
  
  // このニーズに関連する末端性能（↑と↓のみ、空白は除く）の数をカウント
  const leafPerformanceIds = new Set(performances.value.filter(p => p.is_leaf).map(p => p.id))
  const relatedPerformancesCount = validNeedPerformanceRelations.value.filter(
    r => r.need_id === needId && leafPerformanceIds.has(r.performance_id)
  ).length
  
  if (relatedPerformancesCount === 0) return 0
  
  // 合計票数を関連性能数で按分
  return totalVotes / relatedPerformancesCount
}

// 性能列ごとの↑票数を集計
function getUpVotesForPerformance(performanceId: string): number {
  let total = 0
  
  validNeedPerformanceRelations.value.forEach(relation => {
    if (relation.performance_id === performanceId && relation.direction === 'up') {
      total += getPerformanceVotesForNeed(relation.need_id, performanceId)
    }
  })
  
  return total
}

// 性能列ごとの↓票数を集計
function getDownVotesForPerformance(performanceId: string): number {
  let total = 0
  
  validNeedPerformanceRelations.value.forEach(relation => {
    if (relation.performance_id === performanceId && relation.direction === 'down') {
      total += getPerformanceVotesForNeed(relation.need_id, performanceId)
    }
  })
  
  return total
}

// Shannon エントロピーを計算
function calculateEntropy(x: number): number {
  if (x === 0 || x === 1) return 0
  return -x * Math.log2(x) - (1 - x) * Math.log2(1 - x)
}

// 有効投票数を計算: I(a,b) = (a+b) * {1 + H(x)} where x = a/(a+b)
function getEffectiveVotesForPerformance(performanceId: string): number {
  const upVotes = getUpVotesForPerformance(performanceId)
  const downVotes = getDownVotesForPerformance(performanceId)
  const total = upVotes + downVotes
  
  if (total === 0) return 0
  
  const x = upVotes / total
  const entropy = calculateEntropy(x)
  
  return total * (1 + entropy)
}

async function toggleStakeholderRelation(stakeholderId: string, needId: string) {
  if (hasStakeholderRelation(stakeholderId, needId)) {
    await projectStore.removeStakeholderNeedRelation(stakeholderId, needId)
  } else {
    await projectStore.addStakeholderNeedRelation(stakeholderId, needId)
  }
}

// 性能×ニーズ関係（存在する性能のみ）
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
  // その行(ニーズ)OR 列(性能)のどちらかに1つもチェックがない場合に黄色
  return uncheckedNeedIds.value.has(needId) || uncheckedPerformanceIds.value.has(performanceId)
}

async function cyclePerformanceRelation(needId: string, performanceId: string) {
  const relation = getPerformanceRelation(needId, performanceId)
  const utility = getUtilityFunction(needId, performanceId)
  
  if (!relation) {
    // 関係がない → ↑を追加
    await projectStore.addNeedPerformanceRelation(needId, performanceId, 'up')
    
    // アーカイブされた効用データがあれば警告状態で復元
    const archived = utilityFunctions.value.find(
      u => u.need_id === needId && u.performance_id === performanceId && u.archived
    )
    if (archived) {
      archived.archived = false
      archived.warning = true
      archived.direction = 'up'
    }
  } else if (relation.direction === 'up') {
    // ↑ → ↓に更新
    await projectStore.updateNeedPerformanceRelation(needId, performanceId, 'down')
    
    // 保存済みの効用データがある場合は警告状態に
    if (utility && utility.saved) {
      utility.warning = true
      utility.direction = 'down'
    }
  } else {
    // ↓ → 削除
    await projectStore.removeNeedPerformanceRelation(needId, performanceId)
    
    // 保存済みの効用データがある場合はアーカイブ
    if (utility && utility.saved) {
      utility.archived = true
      utility.warning = false
    }
  }
}

function navigateToPerformanceManagement() {
  emit('navigateToPerformance')
}

// 効用関数管理
function getUtilityFunction(needId: string, performanceId: string): UtilityFunction | undefined {
  const result = utilityFunctions.value.find(
    u => u.need_id === needId && u.performance_id === performanceId && !u.archived
  )
  
  // デバッグログは削除（正常に動作することが確認できたため）
  // if (!result && utilityFunctions.value.length > 0) {
  //   // [NeedPerformanceMatrix] 効用関数が見つかりません: {
  //     探しているneed_id: needId,
  //     探しているperformance_id: performanceId,
  //     利用可能な効用関数数: utilityFunctions.value.length,
  //     最初の効用関数: utilityFunctions.value[0]
  //   })
  // }
  
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
  event.stopPropagation() // セルのクリックイベントを止める
  
  const buttonType = getUtilityButtonType(needId, performanceId)
  if (buttonType === 'none') return
  
  // 同じ性能列の他のセルに既に設定があるか確認（列基準を取得）
  const sameColumnFunctions = utilityFunctions.value.filter(
    u => u.performance_id === performanceId && u.saved
  )
  
  // 列基準となる効用関数（最初に見つかったもの）
  const columnStandard = sameColumnFunctions.length > 0 ? sameColumnFunctions[0] : null
  
  // まずローカルのデータを試す
  let utility = getUtilityFunction(needId, performanceId)
  
  // ローカルにない場合はバックエンドからロード
  if (!utility) {
    try {
      const loadedUtility = await projectStore.getUtilityFunction(needId, performanceId)
      if (loadedUtility) {
        utility = loadedUtility
        // ローカルにも追加
        utilityFunctions.value.push(loadedUtility)
      }
    } catch (error) {
      console.error('効用関数の読み込みに失敗しました:', error)
    }
  }
  
  // 列基準がある場合は、type/軸範囲/離散値を強制的に合わせる
  const effectiveType = columnStandard?.type || utility?.type || 'continuous'
  
  currentUtilityEdit.value = {
    needId,
    performanceId,
    type: effectiveType
  }
  
  // 横軸範囲の初期化
  if (effectiveType === 'continuous') {
    if (columnStandard?.axisMin !== undefined && columnStandard?.axisMax !== undefined) {
      // 列基準がある場合はそれを使用
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
  
  // 既存の点をロード（points自体は個別だが、軸範囲は統一）
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
  
  // 離散関数の行データをロード
  if (effectiveType === 'discrete') {
    if (columnStandard?.discreteRows && columnStandard.discreteRows.length > 0) {
      // 列基準がある場合はそれを使用（選択肢は統一、値は個別）
      const standardLabels = columnStandard.discreteRows.map(r => r.label)
      
      if (utility?.discreteRows && utility.discreteRows.length > 0) {
        // 既存データがある場合、ラベルは列基準に合わせ、値は既存のものを使用
        discreteRows.value = standardLabels.map(label => {
          const existing = utility.discreteRows?.find(r => r.label === label)
          return {
            label,
            value: existing?.value ?? 0
          }
        })
      } else {
        // 既存データがない場合、列基準のラベルで値0で初期化
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
  
  // 背景のスクロールを無効化
  document.body.style.overflow = 'hidden'
  
  // モーダルがDOMに追加された後にスライダーを初期化
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
  
  // 背景のスクロールを再有効化
  document.body.style.overflow = ''
}

async function saveUtilityFunction() {
  if (!currentUtilityEdit.value) return
  
  const { needId, performanceId } = currentUtilityEdit.value
  const relation = getPerformanceRelation(needId, performanceId)
  if (!relation) return
  
  // 同じ性能列の全ての関係を取得
  const sameColumnRelations = currentProject.value?.need_performance_relations.filter(
    r => r.performance_id === performanceId
  ) || []
  
  // 保存する効用関数データを作成
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
    // 現在のセルの効用関数を保存
    await projectStore.saveUtilityFunction(needId, performanceId, utilityData)
    
    // ローカルの状態を更新
    const existingIndex = utilityFunctions.value.findIndex(
      u => u.need_id === needId && u.performance_id === performanceId
    )
    
    if (existingIndex >= 0) {
      utilityFunctions.value[existingIndex] = utilityData
    } else {
      utilityFunctions.value.push(utilityData)
    }
    
    // 同じ列（同じ性能）の他のセルには、軸の範囲（axisMin, axisMax）のみを同期
    for (const rel of sameColumnRelations) {
      if (rel.need_id === needId) continue; // 現在のセルはスキップ
      
      // 既存の効用関数を取得
      const existingFunc = utilityFunctions.value.find(
        u => u.need_id === rel.need_id && u.performance_id === performanceId
      )
      
      if (existingFunc) {
        // 既存の効用関数がある場合、軸の範囲のみ更新
        const updatedData: UtilityFunction = {
          ...existingFunc,
          axisMin: utilityData.axisMin,
          axisMax: utilityData.axisMax
          // points, discreteRowsはそのまま保持
        }
        
        await projectStore.saveUtilityFunction(rel.need_id, performanceId, updatedData)
        
        // ローカルの状態も更新
        const idx = utilityFunctions.value.findIndex(
          u => u.need_id === rel.need_id && u.performance_id === performanceId
        )
        if (idx >= 0) {
          utilityFunctions.value[idx] = updatedData
        }
      }
      // 効用関数が未設定のセルには何もしない
    }
    
    closeUtilityModal()
  } catch (error) {
    console.error('効用関数の保存に失敗しました:', error)
    alert('効用関数の保存に失敗しました。')
  }
}

async function resetUtilityFunction() {
  if (!currentUtilityEdit.value) return
  
  if (!confirm('効用関数データを初期化しますか？この操作は取り消せません。')) {
    return
  }
  
  const { needId, performanceId } = currentUtilityEdit.value
  
  try {
    // バックエンドから削除（DELETEメソッドを使用）
    const projectId = projectStore.currentProject?.id
    if (!projectId) {
      throw new Error('プロジェクトIDが取得できません')
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
      throw new Error('削除に失敗しました')
    }
    
    // ローカルからも削除
    const index = utilityFunctions.value.findIndex(
      u => u.need_id === needId && u.performance_id === performanceId
    )
    
    if (index >= 0) {
      utilityFunctions.value.splice(index, 1)
    }
    
    closeUtilityModal()
  } catch (error) {
    console.error('効用関数の削除に失敗しました:', error)
    alert('効用関数の削除に失敗しました。')
  }
}

function getCurrentPerformanceUnit(): string | undefined {
  if (!currentUtilityEdit.value) return undefined
  
  const performance = performances.value.find(
    p => p.id === currentUtilityEdit.value!.performanceId
  )
  
  return performance?.unit
}

// プロジェクトの効用関数を全てロード
async function loadAllUtilityFunctions() {
  if (!currentProject.value?.id) return
  
  try {
    const loadedFunctions = await projectStore.loadUtilityFunctions()
    utilityFunctions.value = loadedFunctions
    
    // 読み込み後、同じ列のデータを統一
    await normalizeUtilityFunctionsByColumn()
  } catch (error) {
    console.error('効用関数のロードに失敗しました:', error)
  }
}

// 同じ性能列の効用関数を統一する（既存データの修正）
async function normalizeUtilityFunctionsByColumn() {
  if (!currentProject.value) return
  
  // 性能IDごとにグループ化
  const performanceGroups = new Map<string, typeof utilityFunctions.value>()
  
  utilityFunctions.value.forEach(uf => {
    if (!performanceGroups.has(uf.performance_id)) {
      performanceGroups.set(uf.performance_id, [])
    }
    performanceGroups.get(uf.performance_id)!.push(uf)
  })
  
  let totalNormalized = 0
  
  // 各性能列ごとに処理
  for (const [performanceId, functions] of performanceGroups.entries()) {
    if (functions.length <= 1) continue
    
    // 最初に見つかった設定を基準とする
    const standard = functions[0]
    
    // 基準と異なる設定を持つものを修正
    for (let i = 1; i < functions.length; i++) {
      const func = functions[i]
      let needsUpdate = false
      
      // 連続値の場合: 軸範囲を統一
      if (standard.type === 'continuous' && func.type === 'continuous') {
        if (func.axisMin !== standard.axisMin || func.axisMax !== standard.axisMax) {
          func.axisMin = standard.axisMin
          func.axisMax = standard.axisMax
          needsUpdate = true
        }
      }
      
      // 離散値の場合: 選択肢（label）を統一、値は保持
      if (standard.type === 'discrete' && func.type === 'discrete') {
        if (standard.discreteRows && func.discreteRows) {
          const standardLabels = standard.discreteRows.map(r => r.label).sort()
          const funcLabels = func.discreteRows.map(r => r.label).sort()
          
          if (JSON.stringify(standardLabels) !== JSON.stringify(funcLabels)) {
            // ラベルを統一、既存の値は保持
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
      
      // typeが異なる場合も統一
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
          console.error(`効用関数の統一に失敗: ${func.need_id} x ${func.performance_id}`, error)
        }
      }
    }
  }
  
  if (totalNormalized > 0) {
  }
}

// プロジェクトが変更されたら効用関数を自動ロード
watch(
  () => currentProject.value?.id,
  (newProjectId) => {
    if (newProjectId) {
      loadAllUtilityFunctions()
    } else {
      // プロジェクトがクリアされたらローカルもクリア
      utilityFunctions.value = []
    }
  },
  { immediate: true }
)

// 分解不足の性能分析
const insufficientDecompositionAnalysis = computed(() => {
  const result = {
    rootLevel: [] as string[],
    leafLevel: [] as string[]
  }
  
  // HHI値を持つ大項目を分析（閾値以上のものを抽出）
  const rootAnalysis = rootGroups.value.map(group => ({
    name: group.rootPerformance.name,
    hhi: getHHIForRoot(group.rootIndex),
    isLeaf: group.rootPerformance.is_leaf
  })).filter(item => item.hhi > 0)
  
  // HHIが高い順にソート
  rootAnalysis.sort((a, b) => b.hhi - a.hhi)
  
  // 平均値を計算
  const avgHHI = rootAnalysis.length > 0 
    ? rootAnalysis.reduce((sum, item) => sum + item.hhi, 0) / rootAnalysis.length 
    : 0
  
  // 平均以上、かつ上位50%を抽出（最大5件）
  const threshold = avgHHI
  const topCount = Math.max(1, Math.ceil(rootAnalysis.length * 0.5))
  result.rootLevel = rootAnalysis
    .filter(item => item.hhi >= threshold)
    .slice(0, Math.min(topCount, 5))
    .map(item => item.name)
  
  // 末端性能のp²値を分析
  const leafAnalysis = getAllPerformanceColumns()
    .filter(perf => perf.is_leaf)
    .map(perf => ({
      name: perf.name,
      pSquared: getPSquaredForPerformance(perf.id)
    }))
    .filter(item => item.pSquared > 0)
  
  // p²が高い順にソート
  leafAnalysis.sort((a, b) => b.pSquared - a.pSquared)
  
  // 平均値を計算
  const avgPSquared = leafAnalysis.length > 0
    ? leafAnalysis.reduce((sum, item) => sum + item.pSquared, 0) / leafAnalysis.length
    : 0
  
  // 平均以上、かつ上位50%を抽出（最大5件）
  const pSquaredThreshold = avgPSquared
  const leafTopCount = Math.max(1, Math.ceil(leafAnalysis.length * 0.5))
  result.leafLevel = leafAnalysis
    .filter(item => item.pSquared >= pSquaredThreshold)
    .slice(0, Math.min(leafTopCount, 5))
    .map(item => item.name)
  
  return result
})

</script>

<style scoped>
.section-header {
  margin-bottom: 20px;
}

.section-header h2 {
  font-size: 24px;
  margin-bottom: 8px;
}

.section-description {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
}

/* ツールバー */
.matrix-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.toolbar-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #495057;
  transition: all 0.2s ease;
}

.toolbar-button:hover {
  background: #e7f1ff;
  border-color: #107c41;
  color: #107c41;
}

.toolbar-button .excel-icon {
  flex-shrink: 0;
}

.toolbar-button span {
  white-space: nowrap;
}

.toolbar-divider {
  width: 1px;
  height: 43px;
  background: #dee2e6;
  margin: 0 8px;
}

.template-download-button:hover {
  box-shadow: 0 2px 6px rgba(16, 124, 65, 0.2);
}

.matrix-image-button {
  color: #6f42c1;
}

.matrix-image-button:hover {
  background: #f3e8ff;
  border-color: #6f42c1;
  color: #6f42c1;
  box-shadow: 0 2px 6px rgba(111, 66, 193, 0.2);
}

.matrix-excel-button {
  color: #107c41;
}

.matrix-excel-button:hover {
  background: #d1f4e0;
  border-color: #107c41;
  color: #107c41;
  box-shadow: 0 2px 6px rgba(16, 124, 65, 0.2);
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

/* 大項目0: 赤系統 */
.performance-header.root-0.level-1 {
  background: #ef9a9a;
}

.performance-header.root-0.level-2 {
  background: #ffcdd2;
}

.performance-header.root-0.level-3 {
  background: #ffebee;
}

/* 大項目1: 青系統 */
.performance-header.root-1.level-1 {
  background: #90caf9;
}

.performance-header.root-1.level-2 {
  background: #bbdefb;
}

.performance-header.root-1.level-3 {
  background: #e3f2fd;
}

/* 大項目2: 緑系統 */
.performance-header.root-2.level-1 {
  background: #a5d6a7;
}

.performance-header.root-2.level-2 {
  background: #c8e6c9;
}

.performance-header.root-2.level-3 {
  background: #e8f5e9;
}

/* 大項目3: 黄系統 */
.performance-header.root-3.level-1 {
  background: #fff59d;
}

.performance-header.root-3.level-2 {
  background: #fff9c4;
}

.performance-header.root-3.level-3 {
  background: #fffde7;
}

/* 大項目4: 紫系統 */
.performance-header.root-4.level-1 {
  background: #e1bee7;
}

.performance-header.root-4.level-2 {
  background: #f3e5f5;
}

.performance-header.root-4.level-3 {
  background: #f8f5fa;
}

/* 大項目5: オレンジ系統 */
.performance-header.root-5.level-1 {
  background: #ffcc80;
}

.performance-header.root-5.level-2 {
  background: #ffe0b2;
}

.performance-header.root-5.level-3 {
  background: #fff3e0;
}

/* 大項目6: シアン系統 */
.performance-header.root-6.level-1 {
  background: #80deea;
}

.performance-header.root-6.level-2 {
  background: #b2ebf2;
}

.performance-header.root-6.level-3 {
  background: #e0f7fa;
}

/* 大項目7: ピンク系統 */
.performance-header.root-7.level-1 {
  background: #f48fb1;
}

.performance-header.root-7.level-2 {
  background: #f8bbd0;
}

.performance-header.root-7.level-3 {
  background: #fce4ec;
}

/* フォールバック（それ以上の大項目） */
.performance-header.level-1 {
  background: #b0bec5;
}

.performance-header.level-2 {
  background: #cfd8dc;
}

.performance-header.level-3 {
  background: #eceff1;
}

/* 末端セルの境界線: デフォルト */
.performance-header.is-leaf {
  border: 2px solid #9c27b0;
  font-weight: 600;
}

/* 末端セルの境界線: 大項目ごと */
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

/* V行セルの背景色: 大項目ごと（ヘッダーと同じ色） */
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

.decomposition-analysis {
  margin-top: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.decomposition-analysis h3 {
  font-size: 18px;
  margin-bottom: 16px;
  color: #333;
}

.analysis-item {
  margin-bottom: 12px;
  line-height: 1.8;
}

.analysis-item strong {
  color: #495057;
  font-weight: 600;
  display: block;
  margin-bottom: 4px;
}

.performance-list {
  color: #e74c3c;
  font-weight: 600;
  font-size: 15px;
}

.analysis-action {
  margin-top: 16px;
  text-align: center;
}

.decompose-button {
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
}

.decompose-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
}

.decompose-button:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
}

.empty-matrix {
  text-align: center;
  padding: 60px 20px;
  color: #999;
  background: #f8f9fa;
  border-radius: 8px;
}

/* 効用関数ボタン */
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

/* モーダル */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  max-width: 800px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.utility-modal h3 {
  margin-bottom: 20px;
  font-size: 20px;
  color: #333;
}

.modal-info {
  background: #f8f9fa;
  padding: 10px 14px;
  border-radius: 6px;
  margin-bottom: 16px;
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
  color: #495057;
  font-size: 12px;
}

.direction-badge {
  background: #667eea;
  color: white;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.graph-section {
  margin-bottom: 20px;
}

.graph-section label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #495057;
  font-size: 14px;
}

.graph-description {
  font-size: 12px;
  color: #6c757d;
  margin-bottom: 12px;
  font-style: italic;
}

.graph-container {
  background: white;
  border: 2px solid #dee2e6;
  border-radius: 8px;
  padding: 12px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
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
  padding: 6px 8px;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #495057;
}

.graph-control-button:hover {
  background: #e9ecef;
  border-color: #adb5bd;
  color: #212529;
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
  margin-top: 8px;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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
  font-size: 14px;
  font-weight: 600;
  color: #212529;
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
  margin-bottom: 8px;
  font-size: 13px;
  color: #495057;
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
  color: #495057;
  margin-right: 4px;
}

.type-button {
  padding: 6px 16px;
  border: 2px solid #dee2e6;
  border-radius: 6px;
  background: white;
  font-size: 13px;
  font-weight: 500;
  color: #495057;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  gap: 6px;
  align-items: center;
}

.type-button:hover {
  border-color: #0066cc;
  background: #f8f9fa;
}

.type-button.active {
  background: #0066cc;
  border-color: #0066cc;
  color: white;
}

.type-icon {
  font-size: 10px;
  font-weight: bold;
}

.axis-range-control {
  margin-top: 16px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.discrete-matrix-control {
  margin-top: 16px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.matrix-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.matrix-label {
  font-size: 14px;
  font-weight: 600;
  color: #495057;
}

.add-row-button {
  padding: 6px 12px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease;
}

.add-row-button:hover {
  background: #2563eb;
}

.discrete-matrix {
  overflow-x: auto;
}

.discrete-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
}

.discrete-table thead {
  background: #e9ecef;
}

.discrete-table th {
  padding: 10px 12px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: #495057;
  border-bottom: 2px solid #dee2e6;
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
  border-bottom: 1px solid #e9ecef;
}

.discrete-row:last-child {
  border-bottom: none;
}

.discrete-row:hover {
  background: #f8f9fa;
}

.label-cell,
.value-cell,
.action-cell {
  padding: 8px 12px;
}

.discrete-input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
  transition: border-color 0.2s ease;
}

.discrete-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.remove-row-button {
  padding: 4px 8px;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.remove-row-button:hover:not(:disabled) {
  background: #b91c1c;
}

.remove-row-button:disabled {
  background: #e5e7eb;
  color: #9ca3af;
  cursor: not-allowed;
}

.matrix-hint {
  margin-top: 12px;
  padding: 10px 12px;
  background: #eff6ff;
  border-left: 3px solid #3b82f6;
  border-radius: 4px;
  font-size: 12px;
  color: #1e40af;
  line-height: 1.5;
}

.range-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.range-label {
  font-size: 14px;
  font-weight: 600;
  color: #495057;
}

.range-tip {
  font-size: 11px;
  color: #6c757d;
  font-style: italic;
}

.range-single-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.range-input {
  padding: 8px 12px;
  border: 2px solid #dee2e6;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  width: 100px;
  transition: border-color 0.2s ease;
}

.range-input:focus {
  outline: none;
  border-color: #0066cc;
}

.nouislider-container {
  flex: 1;
  height: 40px;
  display: flex;
  align-items: center;
}

/* noUiSliderのカスタムスタイル */
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
  gap: 12px;
  justify-content: flex-end;
  align-items: center;
}

.modal-actions .spacer {
  flex: 1;
}

.modal-actions button {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.modal-actions .secondary {
  background: #e9ecef;
  color: #495057;
  border: 1px solid #dee2e6;
}

.modal-actions .secondary:hover {
  background: #dee2e6;
}

.modal-actions .primary {
  background: #667eea;
  color: white;
  border: none;
}

.modal-actions .primary:hover {
  background: #5568d3;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}

.modal-actions .danger {
  background: #fee;
  color: #dc3545;
  border: 2px solid #dc3545;
  font-weight: 700;
}

.modal-actions .danger:hover {
  background: #dc3545;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(220, 53, 69, 0.3);
}
</style>