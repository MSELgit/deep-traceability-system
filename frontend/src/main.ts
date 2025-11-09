// frontend/src/main.ts

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

// Font Awesome
import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { 
	faPenToSquare, faTrash, faEye, faCopy, faRotateRight,
	faHexagonNodes, faExpand, faAlignJustify, faFloppyDisk, faArrowPointer,
	faFolder, faFolderOpen, faShareFromSquare, faFileImport
} from '@fortawesome/free-solid-svg-icons'

// アイコンをライブラリに追加
library.add(
	faPenToSquare, faTrash, faEye, faCopy, faRotateRight,
	faHexagonNodes, faExpand, faAlignJustify, faFloppyDisk, faArrowPointer,
	faFolder, faFolderOpen, faShareFromSquare, faFileImport
)

const app = createApp(App)

// Font Awesomeコンポーネントをグローバル登録
app.component('FontAwesomeIcon', FontAwesomeIcon)

app.use(createPinia())
app.use(router)

app.mount('#app')
