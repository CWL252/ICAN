<template>
  <div class="home-page px-4 sm:px-6 lg:px-8 py-6">
    <transition name="toast-slide">
      <div v-if="statusMessage" :class="['top-toast', statusType === 'error' ? 'error' : 'success']">
        <i class="fas" :class="statusType === 'error' ? 'fa-circle-exclamation' : 'fa-circle-check'"></i>
        <span>{{ statusMessage }}</span>
      </div>
    </transition>

    <!-- 入口模式:个人信息 + 统计 + 两大类入口 -->
    <template v-if="!expandedSection">
      <section class="bg-white rounded-lg shadow-md p-6 mb-6">
        <div class="flex items-center gap-5 flex-wrap">
          <div
            class="w-16 h-16 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-2xl font-bold shrink-0"
          >
            {{ (currentUser?.username || '?').charAt(0).toUpperCase() }}
          </div>
          <div class="min-w-0">
            <div class="flex items-center gap-3 flex-wrap">
              <h1 class="text-2xl font-bold text-gray-800">{{ currentUser?.username || '用户' }}</h1>
              <button class="btn-primary !py-1.5 !px-3 text-sm" @click="openCreateModal">
                <i class="fas fa-plus mr-1"></i>创建项目
              </button>
            </div>
            <p class="text-gray-500 text-sm mt-1">{{ currentUser?.email }}</p>
            <p class="text-gray-500 text-sm mt-1">
              <i class="fas fa-hospital mr-1 text-blue-400"></i>
              <span
                class="inline-flex items-center gap-1 cursor-pointer hover:text-sky-600 hover:underline"
                :title="currentUser?.hospital ? '点击修改医院' : '点击填写医院'"
                @click="openHospitalModal"
              >
                {{ currentUser?.hospital || '未填写医院' }}
                <i class="fas fa-pen text-xs text-slate-300"></i>
              </span>
            </p>
            <p class="text-gray-500 text-sm mt-1">
              <i class="fas fa-calendar mr-1 text-slate-400"></i>加入于 {{ formatJoinDate(currentUser?.created_at) }}
            </p>
          </div>
          <div class="ml-auto shrink-0">
            <template v-if="currentUser?.hasLicense">
              <div class="relative inline-block">
                <img
                  :src="licenseUrl()"
                  alt="医师资格证"
                  class="w-28 rounded-lg border border-slate-200 cursor-pointer hover:opacity-80"
                  title="点击查看大图"
                  @click="openLicenseImage()"
                />
                <button
                  class="absolute -bottom-1.5 -right-1.5 w-7 h-7 rounded-full bg-sky-500 text-white text-xs flex items-center justify-center shadow-md hover:bg-sky-600 transition"
                  title="更换照片"
                  :disabled="licenseUploading"
                  @click="licenseInputRef?.click()"
                >
                  <i class="fas fa-camera"></i>
                </button>
              </div>
              <p class="text-xs text-gray-400 mt-1 text-center">医师资格证</p>
            </template>
            <button
              v-else
              class="w-28 h-16 rounded-lg border border-dashed border-sky-300 bg-sky-50 flex items-center justify-center text-xs text-sky-500 transition hover:bg-sky-100 cursor-pointer"
              title="点击上传医师资格证"
              :disabled="licenseUploading"
              @click="licenseInputRef?.click()"
            >
              <i class="fas fa-upload mr-1"></i>{{ licenseUploading ? '上传中...' : '未上传资格证' }}
            </button>
            <input
              ref="licenseInputRef"
              type="file"
              accept=".jpg,.jpeg,.png,.webp"
              class="hidden"
              @change="onLicenseUploaded"
            />
          </div>
        </div>
      </section>

      <!-- 修改医院弹窗 -->
      <div
        v-if="showHospitalModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4"
        @click.self="closeHospitalModal"
      >
        <div class="modal-panel bg-white rounded-2xl shadow-2xl w-full max-w-sm">
          <h3 class="text-lg font-semibold text-slate-800 mb-4">修改医院</h3>
          <label class="input-label">医院名称</label>
          <input
            v-model="hospitalInput"
            type="text"
            maxlength="60"
            placeholder="请输入所在医院"
            class="input w-full mb-4"
            @keyup.enter="saveHospital"
          />
          <div class="flex justify-end gap-2">
            <button class="btn-secondary" @click="closeHospitalModal">取消</button>
            <button class="btn-primary" :disabled="hospitalSaving" @click="saveHospital">
              {{ hospitalSaving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>

      <section class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="bg-white rounded-lg shadow-md p-5">
          <p class="text-sm text-gray-500">项目总数</p>
          <p class="text-3xl font-bold text-slate-800 mt-2">{{ projects.length }}</p>
        </div>
        <div class="bg-white rounded-lg shadow-md p-5">
          <p class="text-sm text-gray-500">网络项目</p>
          <p class="text-3xl font-bold text-sky-600 mt-2">{{ networkProjects.length }}</p>
        </div>
        <div class="bg-white rounded-lg shadow-md p-5">
          <p class="text-sm text-gray-500">个人手术项目</p>
          <p class="text-3xl font-bold text-blue-600 mt-2">{{ personalProjects.length }}</p>
        </div>
      </section>

      <!-- 分类入口:点击进入对应项目列表 -->
      <section class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <button class="entry-card" @click="goToSection('network')">
          <i class="fas fa-globe text-3xl text-sky-500"></i>
          <div class="min-w-0">
            <p class="text-lg font-bold text-slate-800">网络项目</p>
            <p class="text-sm text-slate-500">{{ networkProjects.length }} 个视频 · 自动记录学习进度</p>
          </div>
          <i class="fas fa-chevron-right text-slate-300 ml-auto"></i>
        </button>
        <button class="entry-card" @click="goToSection('personal')">
          <i class="fas fa-user-doctor text-3xl text-blue-500"></i>
          <div class="min-w-0">
            <p class="text-lg font-bold text-slate-800">个人手术项目</p>
            <p class="text-sm text-slate-500">{{ personalProjects.length }} 个视频 · 按术式小类分组</p>
          </div>
          <i class="fas fa-chevron-right text-slate-300 ml-auto"></i>
        </button>
      </section>
    </template>

    <!-- 列表模式:点击入口进入的独立列表页(创建项目统一在个人主页入口) -->
    <template v-else>
      <div class="flex items-center gap-3 mb-6 flex-wrap">
        <button class="btn-secondary !py-1.5 !px-3" @click="goHome">
          <i class="fas fa-arrow-left mr-1"></i>返回个人主页
        </button>
        <h1 class="text-2xl font-bold text-gray-800">
          {{ expandedSection === 'network' ? '网络项目' : '个人手术项目' }}
        </h1>
        <span class="text-sm text-gray-400">
          共 {{ (expandedSection === 'network' ? networkProjects : personalProjects).length }} 个视频
        </span>
      </div>

    <!-- 网络项目列表:按术式小类分组,记录观看进度与累计学习时长 -->
    <section v-if="expandedSection === 'network'" class="bg-white rounded-lg shadow-md p-6">
      <div class="flex items-center justify-between mb-4 flex-wrap gap-3">
        <h2 class="text-xl font-semibold text-gray-800">
          <i class="fas fa-globe mr-2 text-sky-500"></i>网络项目
        </h2>
      </div>

      <div v-if="!networkProjects.length" class="text-sm text-slate-400">
        <i class="fas fa-globe mr-1 text-sky-400"></i>
        暂无网络项目 —— 点“创建项目”选择“网络”来源即可添加
      </div>

      <div v-else>
        <div v-for="group in networkGroups" :key="group.name" class="mb-8 last:mb-0">
          <div class="flex items-center gap-3 mb-3 flex-wrap">
            <h3 class="text-lg font-semibold text-slate-800">{{ group.name }}</h3>
            <span class="text-xs rounded-full px-3 py-1 bg-slate-100 text-slate-600">
              {{ group.items.length }} 个视频
            </span>
          </div>

          <div class="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3 gap-4">
            <article
              v-for="project in group.items"
              :key="project.id"
              class="project-card border border-slate-200 rounded-xl p-5 bg-slate-50 hover:bg-white transition-colors cursor-pointer"
              @click="openAnalysis(project)"
            >
              <div class="flex justify-between items-start gap-4">
                <div>
                  <h3 class="text-lg font-bold text-slate-800">{{ project.title }}</h3>
                  <p class="text-sm text-slate-500 mt-1">{{ project.procedure || '未填写术式' }}</p>
                </div>
                <span class="flex items-center gap-2 shrink-0">
                  <span class="text-xs rounded-full px-3 py-1 bg-sky-100 text-sky-700">
                    <i class="fas fa-globe mr-1"></i>网络
                  </span>
                  <span
                    class="text-xs rounded-full px-3 py-1"
                    :class="statusClass(project.status)"
                  >
                    {{ project.status || '待分析' }}
                  </span>
                </span>
              </div>

              <p class="text-sm mt-3 rounded-lg bg-sky-50 text-sky-700 px-3 py-2">
                <i class="fas fa-book-open mr-1"></i>
                {{ formatLearningProgress(project.learningProgress) }}
              </p>

              <div class="grid grid-cols-2 gap-3 text-sm text-slate-600 mt-3">
                <div>
                  <p class="text-slate-400">视频文件</p>
                  <p class="font-medium break-all">{{ project.fileName || '未上传' }}</p>
                </div>
                <div>
                  <p class="text-slate-400">视频时长</p>
                  <p class="font-medium">{{ project.duration || '待补充' }}</p>
                </div>
              </div>

              <p v-if="project.description" class="text-sm text-slate-600 mt-4 line-clamp-3">
                {{ project.description }}
              </p>

              <div class="flex gap-3 mt-5 flex-wrap">
                <button class="btn-secondary" @click.stop="removeProjectItem(project)">
                  <i class="fas fa-trash mr-2"></i>删除项目
                </button>
                <button class="btn-secondary" @click.stop="editProject(project)">
                  <i class="fas fa-copy mr-2"></i>修改信息
                </button>
              </div>
            </article>
          </div>
        </div>
      </div>
    </section>

    <!-- 个人手术项目列表:按术式小类分组,同小类多个视频展示成长曲线 -->
    <section v-else class="bg-white rounded-lg shadow-md p-6">
      <div class="flex items-center justify-between mb-4 flex-wrap gap-3">
        <h2 class="text-xl font-semibold text-gray-800">
          <i class="fas fa-user-doctor mr-2 text-blue-500"></i>个人手术项目
        </h2>
      </div>

      <div v-if="!personalProjects.length" class="text-sm text-slate-400">
        <i class="fas fa-user-doctor mr-1 text-blue-400"></i>
        暂无个人手术项目 —— 点“创建项目”选择“个人”来源即可添加
      </div>

      <div v-else>
        <div v-for="group in personalGroups" :key="group.name" class="mb-8 last:mb-0">
          <div class="flex items-center gap-3 mb-3 flex-wrap">
            <h3 class="text-lg font-semibold text-slate-800">{{ group.name }}</h3>
            <span class="text-xs rounded-full px-3 py-1 bg-slate-100 text-slate-600">
              {{ group.items.length }} 个视频
            </span>
          </div>

          <!-- 成长曲线:与项目卡片同宽,紧凑展示;≥2 个视频画曲线,1 个时显示提示 -->
          <GrowthCurve :points="curvePointsFor(group.name)" class="mb-3 max-w-[450px]" />

          <div class="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3 gap-4">
            <article
              v-for="project in group.items"
              :key="project.id"
              class="project-card border border-slate-200 rounded-xl p-5 bg-slate-50 hover:bg-white transition-colors cursor-pointer"
              @click="openAnalysis(project)"
            >
              <div class="flex justify-between items-start gap-4">
                <div>
                  <h3 class="text-lg font-bold text-slate-800">{{ project.title }}</h3>
                  <p class="text-sm text-slate-500 mt-1">{{ project.procedure || '未填写术式' }}</p>
                </div>
                <span class="flex items-center gap-2 shrink-0">
                  <span
                    v-if="getSharedCommunityId(project.id)"
                    class="text-xs rounded-full px-3 py-1 bg-emerald-100 text-emerald-700"
                  >
                    <i class="fas fa-share-nodes mr-1"></i>已分享
                  </span>
                  <span
                    class="text-xs rounded-full px-3 py-1"
                    :class="statusClass(project.status)"
                  >
                    {{ project.status || '待分析' }}
                  </span>
                </span>
              </div>

              <div class="grid grid-cols-2 gap-3 text-sm text-slate-600 mt-4">
                <div>
                  <p class="text-slate-400">术者</p>
                  <p class="font-medium">{{ project.surgeon || '未填写' }}</p>
                </div>
                <div>
                  <p class="text-slate-400">上传日期</p>
                  <p class="font-medium">{{ project.date || '未填写' }}</p>
                </div>
                <div>
                  <p class="text-slate-400">视频文件</p>
                  <p class="font-medium break-all">{{ project.fileName || '未上传' }}</p>
                </div>
                <div>
                  <p class="text-slate-400">视频时长</p>
                  <p class="font-medium">{{ project.duration || '待补充' }}</p>
                </div>
              </div>

              <p v-if="project.description" class="text-sm text-slate-600 mt-4 line-clamp-3">
                {{ project.description }}
              </p>

              <div class="flex gap-3 mt-5 flex-wrap">
                <button class="btn-secondary" @click.stop="removeProjectItem(project)">
                  <i class="fas fa-trash mr-2"></i>删除项目
                </button>
                <button class="btn-secondary" @click.stop="editProject(project)">
                  <i class="fas fa-copy mr-2"></i>修改信息
                </button>
                <button
                  class="btn-secondary"
                  @click.stop="openShareModal(project)"
                >
                  <i class="fas fa-share-nodes mr-2"></i>
                  {{ getSharedCommunityId(project.id) ? '更新分享' : '分享到社区' }}
                </button>
                <button
                  v-if="getSharedCommunityId(project.id)"
                  class="btn-secondary text-red-600"
                  @click.stop="cancelShare(project)"
                >
                  <i class="fas fa-ban mr-2"></i>取消分享
                </button>
              </div>
            </article>
          </div>
        </div>
      </div>
    </section>
    </template>

    <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4">
      <div class="modal-panel bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between border-b border-slate-200 px-6 py-5">
          <div>
            <h2 class="text-2xl font-bold text-slate-800">{{ editingProjectId ? '修改视频项目' : '创建视频项目' }}</h2>
            <p class="text-sm text-slate-500 mt-1">{{ editingProjectId ? '修改项目描述和视频信息，保存后会更新原项目。' : '填写项目描述并上传视频，创建后会直接进入对应的分析页。' }}</p>
          </div>
          <button class="text-slate-400 hover:text-slate-700" @click="closeCreateModal">
            <i class="fas fa-xmark text-2xl"></i>
          </button>
        </div>

        <div class="p-6 pb-0">
          <label class="input-label">视频来源 <span class="required-mark">*</span></label>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <button
              type="button"
              class="source-card"
              :class="form.videoSource === 'personal' ? 'source-card-active' : ''"
              :disabled="!!editingProjectId"
              @click="form.videoSource = 'personal'"
            >
              <i class="fas fa-user-doctor mr-2 text-blue-500"></i>
              <span class="font-semibold">个人</span>
              <span class="block text-xs text-slate-500 mt-1">自己的手术视频，记录成长曲线</span>
            </button>
            <button
              type="button"
              class="source-card"
              :class="form.videoSource === 'network' ? 'source-card-active' : ''"
              :disabled="!!editingProjectId"
              @click="form.videoSource = 'network'"
            >
              <i class="fas fa-globe mr-2 text-sky-500"></i>
              <span class="font-semibold">网络</span>
              <span class="block text-xs text-slate-500 mt-1">网络获取的教学视频，记录学习进度</span>
            </button>
          </div>
          <p v-if="editingProjectId" class="text-xs text-slate-400 mt-2">
            <i class="fas fa-lock mr-1"></i>视频来源创建后不可更改
          </p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
          <div class="space-y-4">
            <div>
              <label class="input-label">术式小类 <span class="required-mark">*</span></label>
              <div class="flex flex-wrap gap-2 mb-2">
                <button
                  v-for="preset in SUBCATEGORY_PRESETS"
                  :key="preset"
                  type="button"
                  class="subcategory-chip"
                  :class="form.subcategory === preset ? 'subcategory-chip-active' : ''"
                  @click="form.subcategory = preset"
                >
                  {{ preset }}
                </button>
              </div>
              <input
                v-model="form.subcategory"
                class="input"
                :class="formErrors.subcategory ? 'input-error' : ''"
                maxlength="20"
                placeholder="或输入自定义术式名称"
                @input="formErrors.subcategory = ''"
              />
              <p v-if="formErrors.subcategory" class="field-error">{{ formErrors.subcategory }}</p>
              <p class="text-xs text-slate-400 mt-1">
                {{
                  form.videoSource === 'personal'
                    ? '同一小类上传多个视频后，可查看成长曲线（视频时长越短越熟练）'
                    : '网络视频按术式小类分组展示'
                }}
              </p>
            </div>
            <div>
              <label class="input-label">项目名称 <span class="required-mark">*</span></label>
              <input
                v-model="form.title"
                class="input"
                :class="formErrors.title ? 'input-error' : ''"
                placeholder="例如：LC-病例-001"
                @input="formErrors.title = ''"
              />
              <p v-if="formErrors.title" class="field-error">{{ formErrors.title }}</p>
            </div>
            <div>
              <label class="input-label">术式名称</label>
              <input v-model="form.procedure" class="input" placeholder="例如：腹腔镜胆囊切除术" />
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="input-label">术者</label>
                <input v-model="form.surgeon" class="input" placeholder="输入术者姓名" />
              </div>
              <div>
                <label class="input-label">科室</label>
                <input v-model="form.department" class="input" placeholder="例如：肝胆外科" />
              </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="input-label">手术日期</label>
                <input v-model="form.date" type="date" class="input" />
              </div>
              <div>
                <label class="input-label">视频时长</label>
                <div class="input bg-slate-50 text-slate-700">
                  {{ form.duration || '上传后自动统计' }}
                </div>
              </div>
            </div>
            <div>
              <label class="input-label">项目描述</label>
              <textarea v-model="form.description" class="input min-h-[140px]" placeholder="填写病例背景、教学目标、分析关注点"></textarea>
            </div>
          </div>

          <div class="space-y-4">
            <div class="border border-dashed border-slate-300 rounded-xl p-6 bg-slate-50">
              <h3 class="text-lg font-semibold text-slate-800 mb-3">视频文件 <span class="required-mark">*</span></h3>
              <button class="btn-primary mb-4" @click="triggerUpload">
                <i class="fas fa-video mr-2"></i>选择手术视频
              </button>
              <input ref="fileInputRef" type="file" accept="video/*" class="hidden" @change="onFileSelected" />
              <p class="text-sm text-slate-500">当前项目的视频将在本次会话内直接用于分析页播放与标注。</p>
              <div v-if="form.fileName" class="mt-4 text-sm text-slate-700">
                <p><span class="text-slate-400">文件名：</span>{{ form.fileName }}</p>
                <p><span class="text-slate-400">视频时长：</span>{{ form.duration || '正在读取...' }}</p>
              </div>
            </div>

            <div class="border border-slate-200 rounded-xl overflow-hidden bg-black">
              <video v-if="form.videoUrl" :src="form.videoUrl" class="w-full h-[280px] object-cover" controls></video>
              <div v-else class="h-[280px] flex items-center justify-center text-slate-400 bg-slate-900">
                上传后可在这里预览视频
              </div>
            </div>

            <div class="flex gap-3 flex-wrap">
              <button class="btn-primary" @click="createProject">
                <i class="fas fa-save mr-2"></i>{{ editingProjectId ? '保存修改' : '创建并进入分析' }}
              </button>
              <button class="btn-secondary" @click="closeCreateModal">
                <i class="fas fa-arrow-left mr-2"></i>取消
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showShareModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4">
      <div class="modal-panel bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between border-b border-slate-200 px-6 py-5">
          <div>
            <h2 class="text-2xl font-bold text-slate-800">
              {{ isSharedProject ? '更新社区分享' : '分享到社区' }}
            </h2>
            <p class="text-sm text-slate-500 mt-1">
              分享后其他用户可以浏览、点赞、收藏并评论你的项目。
            </p>
          </div>
          <button class="text-slate-400 hover:text-slate-700" @click="closeShareModal">
            <i class="fas fa-xmark text-2xl"></i>
          </button>
        </div>

        <div class="p-6 space-y-4">
          <div>
            <label class="input-label">分享标题 <span class="required-mark">*</span></label>
            <input
              v-model="shareForm.title"
              class="input"
              :class="shareErrors.title ? 'input-error' : ''"
              placeholder="社区里展示的项目名称"
              @input="shareErrors.title = ''"
            />
            <p v-if="shareErrors.title" class="field-error">{{ shareErrors.title }}</p>
          </div>
          <div>
            <label class="input-label">项目分类 <span class="required-mark">*</span></label>
            <div class="grid grid-cols-2 gap-3">
              <select v-model="shareForm.category" class="input" @change="onCategoryGroupChange">
                <option v-for="group in categoryGroups" :key="group.name" :value="group.name">
                  {{ group.name }}
                </option>
              </select>
              <select v-model="shareForm.subcategory" class="input">
                <option v-for="sub in currentSubcategories" :key="sub" :value="sub">
                  {{ sub }}
                </option>
              </select>
            </div>
            <p class="text-xs text-slate-400 mt-1.5">先选大类，再选具体术式，方便大家在开源广场按分类浏览。</p>
          </div>
          <div>
            <label class="input-label">项目描述</label>
            <textarea
              v-model="shareForm.description"
              class="input min-h-[100px]"
              placeholder="向社区介绍这个病例的背景、看点或分析心得"
            ></textarea>
          </div>

          <div v-if="hasAnalysisResult" class="border border-slate-200 rounded-xl p-4 bg-slate-50">
            <label class="flex items-center gap-3 cursor-pointer">
              <input v-model="shareIncludePredictions" type="checkbox" class="w-4 h-4 accent-blue-600" />
              <span class="text-sm font-semibold text-slate-700">包含逐帧预测数据</span>
            </label>
            <p class="text-xs text-slate-500 mt-2 leading-relaxed">
              逐帧预测数据体积较大（可能超过 2MB 上限）。不勾选时仅分享阶段分析结果、
              人工修正片段与器械统计，社区详情页仍可正常展示分析结论。
            </p>
          </div>

          <div v-else class="border border-amber-200 rounded-xl p-4 bg-amber-50 text-sm text-amber-700">
            <i class="fas fa-circle-info mr-1"></i>
            该项目还没有分析结果，将只分享元数据信息。
          </div>

          <div v-if="shareProjectHasVideo" class="border border-slate-200 rounded-xl p-4 bg-slate-50">
            <label class="flex items-center gap-3 cursor-pointer">
              <input v-model="shareIncludeVideo" type="checkbox" class="w-4 h-4 accent-blue-600" />
              <span class="text-sm font-semibold text-slate-700">包含手术视频</span>
            </label>
            <p class="text-xs text-slate-500 mt-2 leading-relaxed">
              手术视频将上传到社区服务器（可能较大，上限 1GB），其他登录用户可在线播放。
            </p>
          </div>

          <div v-if="sharingPhase === 'video'" class="border border-blue-200 rounded-xl p-4 bg-blue-50">
            <div class="flex justify-between text-xs text-blue-700 mb-2">
              <span><i class="fas fa-upload mr-1"></i>正在上传手术视频</span>
              <span class="font-bold">{{ shareUploadProgress }}%</span>
            </div>
            <div class="h-2 bg-white rounded-full overflow-hidden">
              <div
                class="h-full bg-blue-600 transition-all duration-150"
                :style="{ width: `${shareUploadProgress}%` }"
              ></div>
            </div>
          </div>

          <div class="flex gap-3">
            <button class="btn-primary" :disabled="shareSubmitting" @click="submitShare">
              <i class="fas fa-share-nodes mr-2"></i>
              <template v-if="sharingPhase === 'video'">上传视频 {{ shareUploadProgress }}%...</template>
              <template v-else-if="shareSubmitting">分享中...</template>
              <template v-else>{{ isSharedProject ? '保存更新' : '发布分享' }}</template>
            </button>
            <button class="btn-secondary" :disabled="shareSubmitting" @click="closeShareModal">
              <i class="fas fa-arrow-left mr-2"></i>取消
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { deleteProject, getProjects, saveProject, setActiveProject, updateProjectField } from '../projectStore'
import { syncRunningProjectsPhaseAnalysis } from '../phaseAnalysisStore'
import { deleteProjectVideo, getProjectVideo, saveProjectVideo } from '../videoStore'
import {
  deleteProject as deleteCommunityProject,
  listCategories,
  shareProject,
  updateProject as updateCommunityProject,
  uploadProjectVideo,
} from '../api/community'
import {
  getSharedCommunityId,
  removeSharedProject,
  setSharedCommunityId,
} from '../communityShareStore'
import { currentUser, setStoredUser } from '../lib/auth'
import { licenseUrl, updateProfile, uploadLicense } from '../api/auth'
import GrowthCurve from '../components/GrowthCurve.vue'

// 术式小类预设(个人项目分组用,也可自由输入自定义名称)
const SUBCATEGORY_PRESETS = [
  '腹腔镜胆囊切除术',
  '阑尾切除术',
  '疝修补术',
  '胆总管探查术',
  '肝切除术',
  '其他',
]

const router = useRouter()
const route = useRoute()
const projects = ref([])
const showCreateModal = ref(false)
const fileInputRef = ref(null)
const form = ref(getEmptyForm())
const formErrors = ref({ title: '' })
const selectedVideoFile = ref(null)
const statusMessage = ref('')
const statusType = ref('success')
const editingProjectId = ref('')
const showShareModal = ref(false)
const shareProjectId = ref('')
const shareForm = ref({ title: '', category: '肝胆外科', subcategory: '胆囊切除术', description: '' })
const categoryGroups = ref([])
const currentSubcategories = computed(() => {
  const group = categoryGroups.value.find((g) => g.name === shareForm.value.category)
  return group ? group.items : []
})

function onCategoryGroupChange() {
  const subs = currentSubcategories.value
  shareForm.value.subcategory = subs.length ? subs[0] : ''
}
const shareErrors = ref({ title: '' })
const shareIncludePredictions = ref(false)
const shareIncludeVideo = ref(true)
const shareUploadProgress = ref(0)
const sharingPhase = ref('') // '' | 'metadata' | 'video'
const shareSubmitting = ref(false)
let syncTimer = null
let durationReadPromise = null
let statusTimer = null

const isSharedProject = computed(() => Boolean(getSharedCommunityId(shareProjectId.value)))
const hasAnalysisResult = computed(() => {
  const project = projects.value.find((item) => item.id === shareProjectId.value)
  return Boolean(project?.phaseAnalysis?.result)
})
const shareProjectHasVideo = computed(() => {
  const project = projects.value.find((item) => item.id === shareProjectId.value)
  return Boolean(project?.hasVideo)
})

// 列表模式:query.section 为 network/personal 时进入对应列表界面,否则为个人主页入口模式
const expandedSection = computed(() => {
  const s = route.query.section
  return s === 'network' || s === 'personal' ? s : null
})
function goToSection(section) {
  router.push({ query: { section } })
}
function goHome() {
  router.push({ query: {} })
}

// 两类项目与按小类分组(旧项目无 videoSource,由 projectStore 兜底为 personal)
const networkProjects = computed(() => projects.value.filter((p) => p.videoSource === 'network'))
const personalProjects = computed(() => projects.value.filter((p) => p.videoSource !== 'network'))
const personalGroups = computed(() => {
  const groups = new Map()
  for (const project of personalProjects.value) {
    const name = project.subcategory?.trim() || '未分类'
    if (!groups.has(name)) groups.set(name, [])
    groups.get(name).push(project)
  }
  return Array.from(groups.entries()).map(([name, items]) => ({ name, items }))
})
// 网络项目同样按术式小类分组展示(无成长曲线,学习进度在卡片内)
const networkGroups = computed(() => {
  const groups = new Map()
  for (const project of networkProjects.value) {
    const name = project.subcategory?.trim() || '未分类'
    if (!groups.has(name)) groups.set(name, [])
    groups.get(name).push(project)
  }
  return Array.from(groups.entries()).map(([name, items]) => ({ name, items }))
})

// 组内按上传时间升序生成曲线点;时长取分析结果 meta,回退解析 duration 字符串
function curvePointsFor(groupName) {
  const group = personalGroups.value.find((g) => g.name === groupName)
  if (!group) return []
  return group.items
    .map((p) => {
      const seconds = durationToSeconds(p)
      if (seconds === null) return null
      const time = p.uploadedAt || p.updatedAt || ''
      return {
        order: Date.parse(time) || 0,
        name: p.title || formatDateShort(time),
        label: formatDateShort(time),
        durationSeconds: seconds,
        durationText: formatDuration(seconds),
      }
    })
    .filter(Boolean)
    .sort((a, b) => a.order - b.order)
}

function durationToSeconds(project) {
  const meta = project.phaseAnalysis?.result?.meta
  if (meta && Number.isFinite(Number(meta.durationSeconds)) && Number(meta.durationSeconds) > 0) {
    return Number(meta.durationSeconds)
  }
  return parseDurationToSeconds(project.duration)
}

// 解析 "mm:ss" / "h:mm:ss" 为秒
function parseDurationToSeconds(duration) {
  if (typeof duration !== 'string') return null
  const parts = duration.trim().split(':')
  if (parts.length < 2 || parts.length > 3) return null
  const nums = parts.map((p) => Number(p))
  if (nums.some((n) => !Number.isFinite(n) || n < 0)) return null
  let total = 0
  for (const n of nums) total = total * 60 + n
  return total > 0 ? total : null
}

function formatDateShort(time) {
  if (!time) return ''
  const d = new Date(time)
  if (Number.isNaN(d.getTime())) return ''
  return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function formatJoinDate(createdAt) {
  if (!createdAt) return '未知'
  return String(createdAt).slice(0, 10)
}

function formatLearningProgress(progress) {
  if (!progress?.studiedSeconds) {
    return '尚未开始学习'
  }
  return `累计学习 ${formatStudied(progress.studiedSeconds)}`
}

function formatStudied(totalSeconds) {
  if (!totalSeconds || totalSeconds <= 0) return '0 分钟'
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  if (hours > 0) return `${hours} 小时 ${minutes} 分`
  return `${minutes} 分`
}

function openLicenseImage() {
  const url = licenseUrl()
  if (url) window.open(url, '_blank')
}

// 修改医院:点击"未填写医院"弹出输入框,保存后刷新个人信息卡
const showHospitalModal = ref(false)
const hospitalInput = ref('')
const hospitalSaving = ref(false)

function openHospitalModal() {
  hospitalInput.value = currentUser.value?.hospital || ''
  showHospitalModal.value = true
}

function closeHospitalModal() {
  showHospitalModal.value = false
  hospitalSaving.value = false
}

async function saveHospital() {
  hospitalSaving.value = true
  try {
    const user = await updateProfile({ hospital: hospitalInput.value.trim() })
    setStoredUser(user)
    currentUser.value = user
    showStatus('医院信息已更新', 'success')
    closeHospitalModal()
  } catch (error) {
    showStatus(error?.message || '保存失败，请重试', 'error')
  } finally {
    hospitalSaving.value = false
  }
}

// 补传/更换医师资格证:点击"未上传资格证"或缩略图上的相机按钮选图,
// 成功后卡片立即切换为最新缩略图(后端 no-cache 保证不命中旧缓存)
const licenseInputRef = ref(null)
const licenseUploading = ref(false)
const LICENSE_ALLOWED_EXTS = ['.jpg', '.jpeg', '.png', '.webp']
const LICENSE_MAX_BYTES = 5 * 1024 * 1024

async function onLicenseUploaded(event) {
  const file = event.target.files?.[0]
  if (!file) return

  const suffix = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
  if (!LICENSE_ALLOWED_EXTS.includes(suffix)) {
    showStatus('资格证仅支持 jpg/jpeg/png/webp 格式', 'error')
    event.target.value = ''
    return
  }
  if (file.size > LICENSE_MAX_BYTES) {
    showStatus('资格证大小不能超过 5MB', 'error')
    event.target.value = ''
    return
  }

  licenseUploading.value = true
  try {
    const user = await uploadLicense(file)
    setStoredUser(user)
    currentUser.value = user
    showStatus('医师资格证上传成功', 'success')
  } catch (error) {
    showStatus(error?.message || '资格证上传失败，请重试', 'error')
  } finally {
    licenseUploading.value = false
    event.target.value = ''
  }
}

function getEmptyForm() {
  return {
    title: '',
    procedure: '',
    surgeon: '',
    department: '',
    date: '',
    duration: '',
    description: '',
    fileName: '',
    videoUrl: '',
    hasVideo: false,
    status: '草稿',
    videoSource: 'personal',
    subcategory: '',
    uploadedAt: '',
    learningProgress: null,
  }
}

function loadProjects() {
  projects.value = getProjects()
}

function statusClass(status) {
  if (status === '草稿') return 'bg-amber-100 text-amber-700'
  if (status === '正在上传') return 'bg-sky-100 text-sky-700'
  if (status === '待分析') return 'bg-slate-100 text-slate-700'
  if (status === '正在分析') return 'bg-blue-100 text-blue-700'
  if (status === '分析完成' || status === '完成') return 'bg-emerald-100 text-emerald-700'
  if (status === '分析失败') return 'bg-red-100 text-red-700'
  return 'bg-slate-100 text-slate-700'
}

function showStatus(message, type = 'success') {
  if (statusTimer) {
    window.clearTimeout(statusTimer)
  }
  statusMessage.value = message
  statusType.value = type
  statusTimer = window.setTimeout(() => {
    statusMessage.value = ''
    statusTimer = null
  }, 2400)
}

function openCreateModal() {
  form.value = getEmptyForm()
  formErrors.value = { title: '' }
  selectedVideoFile.value = null
  editingProjectId.value = ''
  durationReadPromise = null
  showCreateModal.value = true
}

function closeCreateModal() {
  if (form.value.videoUrl && form.value.videoUrl.startsWith('blob:')) {
    URL.revokeObjectURL(form.value.videoUrl)
  }
  selectedVideoFile.value = null
  editingProjectId.value = ''
  durationReadPromise = null
  showCreateModal.value = false
}

function triggerUpload() {
  fileInputRef.value?.click()
}

async function onFileSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return
  selectedVideoFile.value = file
  formErrors.value.title = ''
  if (form.value.videoUrl && form.value.videoUrl.startsWith('blob:')) {
    URL.revokeObjectURL(form.value.videoUrl)
  }
  form.value.fileName = file.name
  form.value.videoUrl = URL.createObjectURL(file)
  form.value.hasVideo = true
  form.value.duration = ''

  try {
    durationReadPromise = readVideoDuration(form.value.videoUrl)
    form.value.duration = await durationReadPromise
  } catch {
    form.value.duration = '无法读取'
  } finally {
    durationReadPromise = null
  }
}

function readVideoDuration(videoUrl) {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    video.preload = 'metadata'
    video.onloadedmetadata = () => {
      resolve(formatDuration(video.duration))
      video.removeAttribute('src')
      video.load()
    }
    video.onerror = () => {
      reject(new Error('视频时长读取失败'))
      video.removeAttribute('src')
      video.load()
    }
    video.src = videoUrl
  })
}

function formatDuration(secondsValue) {
  if (!Number.isFinite(secondsValue) || secondsValue < 0) {
    return ''
  }

  const totalSeconds = Math.round(secondsValue)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

async function createProject() {
  if (!form.value.title.trim()) {
    formErrors.value.title = '请填写项目名称'
    showStatus('请先填写必填项：项目名称', 'error')
    return
  }
  if (!form.value.subcategory.trim()) {
    formErrors.value.subcategory = '请选择或输入术式小类'
    showStatus('请先选择或输入术式小类', 'error')
    return
  }
  if (durationReadPromise) {
    try {
      form.value.duration = await durationReadPromise
    } catch {
      form.value.duration = form.value.duration || '无法读取'
    }
  }

  const now = new Date()
  const isEditing = Boolean(editingProjectId.value)
  const projectId = editingProjectId.value || `project-${now.getTime()}`
  let project = {
    ...form.value,
    id: projectId,
    hasVideo: Boolean(selectedVideoFile.value) || Boolean(form.value.hasVideo),
    videoUrl: '',
    status: selectedVideoFile.value ? '正在上传' : form.value.status,
    // 成长曲线排序键:创建时落一次,编辑不覆盖
    uploadedAt: isEditing ? form.value.uploadedAt || now.toISOString() : now.toISOString(),
    updatedAt: now.toISOString(),
    updatedAtLabel: now.toLocaleString('zh-CN'),
  }

  saveProject(project)

  if (selectedVideoFile.value) {
    await saveProjectVideo(projectId, selectedVideoFile.value)
    project = {
      ...project,
      status: '待分析',
      updatedAt: new Date().toISOString(),
      updatedAtLabel: new Date().toLocaleString('zh-CN'),
    }
  }

  saveProject(project)
  setActiveProject(project)
  loadProjects()
  closeCreateModal()
  if (isEditing) {
    showStatus('项目信息已更新', 'success')
  } else {
    router.push('/analysis')
  }
}

function openAnalysis(project) {
  saveProject(project)
  setActiveProject(project)
  router.push('/analysis')
}

async function editProject(project) {
  if (form.value.videoUrl && form.value.videoUrl.startsWith('blob:')) {
    URL.revokeObjectURL(form.value.videoUrl)
  }
  form.value = {
    title: project.title || '',
    procedure: project.procedure || '',
    surgeon: project.surgeon || '',
    department: project.department || '',
    date: project.date || '',
    duration: project.duration || '',
    description: project.description || '',
    fileName: project.fileName || '',
    videoUrl: '',
    hasVideo: Boolean(project.hasVideo),
    status: project.status || '草稿',
    phaseAnalysis: project.phaseAnalysis || null,
    instrumentStats: project.instrumentStats || null,
    notes: project.notes || [],
    videoSource: project.videoSource === 'network' ? 'network' : 'personal',
    subcategory: project.subcategory || '',
    uploadedAt: project.uploadedAt || '',
    learningProgress: project.learningProgress || null,
  }
  editingProjectId.value = project.id
  formErrors.value = { title: '' }
  selectedVideoFile.value = null
  durationReadPromise = null
  showCreateModal.value = true

  if (project.hasVideo || project.fileName) {
    try {
      const file = await getProjectVideo(project.id)
      if (file && editingProjectId.value === project.id) {
        form.value.videoUrl = URL.createObjectURL(file)
      } else if (editingProjectId.value === project.id) {
        showStatus('未找到原视频文件，请重新上传', 'error')
      }
    } catch {
      if (editingProjectId.value === project.id) {
        showStatus('原视频加载失败，请重新上传', 'error')
      }
    }
  }
}

async function removeProjectItem(project) {
  // 若该项目已分享到社区，同步取消分享（后端会连带删除视频文件），避免留下孤儿数据
  const communityProjectId = getSharedCommunityId(project.id)
  await deleteProjectVideo(project.id)
  deleteProject(project.id)
  if (communityProjectId) {
    try {
      await deleteCommunityProject(communityProjectId)
      removeSharedProject(project.id)
    } catch (error) {
      showStatus(`本地项目已删除，但取消社区分享失败：${error.message || '请稍后重试'}`, 'error')
    }
  }
  loadProjects()
}

function openShareModal(project) {
  shareProjectId.value = project.id
  shareForm.value = {
    title: project.title || '',
    category: '肝胆外科',
    subcategory: '胆囊切除术',
    description: project.description || '',
  }
  shareErrors.value = { title: '' }
  shareIncludePredictions.value = false
  shareIncludeVideo.value = Boolean(project.hasVideo)
  shareUploadProgress.value = 0
  sharingPhase.value = ''
  showShareModal.value = true
}

function closeShareModal() {
  showShareModal.value = false
  shareProjectId.value = ''
}

function buildSharePayload(project) {
  const phaseAnalysis = project.phaseAnalysis || null
  let phasePayload = null

  if (phaseAnalysis) {
    const result = phaseAnalysis.result || null
    const clippedResult = result ? { ...result } : null
    // 逐帧预测数据体积大，默认裁剪，仅保留阶段结论相关字段
    if (clippedResult && !shareIncludePredictions.value) {
      delete clippedResult.predictions
    }
    phasePayload = {
      result: clippedResult,
      editedSegments: phaseAnalysis.editedSegments || [],
      instrumentStats: project.instrumentStats || null,
      report: buildShareReport(project),
    }
  }

  return {
    title: shareForm.value.title.trim(),
    category: shareForm.value.category || '肝胆外科',
    subcategory: shareForm.value.subcategory || '胆囊切除术',
    procedure: project.procedure || '',
    surgeon: project.surgeon || '',
    department: project.department || '',
    date: project.date || '',
    duration: project.duration || '',
    description: shareForm.value.description.trim(),
    fileName: project.fileName || '',
    status: project.status || '分析完成',
    phaseAnalysis: phasePayload,
  }
}

// 分享时携带完整 AI 分析报告(总结/关键指标/操作评估/关键问题/改进建议),与本地分析页报告逻辑一致
function buildShareReport(project) {
  const result = project.phaseAnalysis?.result || null
  const steps = result?.steps || []
  const stepCount = project.phaseAnalysis?.editedSegments?.length || steps.length
  const instrumentItems = project.instrumentStats?.items || []
  const statsLoading = project.instrumentStats?.status === 'loading'
  const hasVideo = Boolean(project.hasVideo)
  const durationSeconds = result?.meta?.durationSeconds || 0

  // 总结(与本地分析页 reportSummary 一致)
  const summary = hasVideo
    ? stepCount
      ? `已识别 ${stepCount} 个关键步骤，结合器械统计和异常检测结果形成当前报告。`
      : '视频已加载，可先执行关键步骤分析，报告内容会结合异常检测和器械统计自动汇总。'
    : '当前项目尚未上传视频，上传后会在这里生成分析摘要。'

  // 关键指标(与本地分析页 reportMetrics 一致)
  const metrics = [
    { label: '视频时长', value: formatReportDuration(durationSeconds) },
    { label: '关键步骤', value: `${stepCount} 个` },
    { label: '异常检测', value: '待接入' },
    {
      label: '器械类型',
      value: statsLoading ? '统计中' : instrumentItems.length ? `${instrumentItems.length} 类` : '待统计',
    },
  ]

  const operationAssessment = hasVideo
    ? [
        '胆囊切除流程整体符合腹腔镜胆囊切除术的常规路径，画面推进围绕胆囊牵拉、胆囊三角显露、管道处理和胆囊床分离等关键阶段展开。',
        steps.length
          ? `系统已识别 ${steps.length} 个关键步骤，可用于术后复盘和教学定位。`
          : '关键步骤识别尚未完成，当前操作评估以预设模板展示。',
        instrumentItems.length
          ? '器械使用以抓持、分离和电凝相关器械为主，使用频率分布与胆囊切除术常见操作节奏基本一致。'
          : '器械统计结果尚未完成，暂无法对器械切换节奏进行量化判断。',
      ]
    : ['尚未上传视频，暂无法形成操作评估。']

  const keyIssues = hasVideo
    ? [
        steps.length
          ? '关键步骤结果仍需结合原始视频逐段复核，尤其关注胆囊三角显露和夹闭前确认阶段。'
          : '关键步骤尚未完成识别，阶段性风险点仍需等待模型输出。',
        statsLoading
          ? '器械统计仍在进行中，暂不能判断是否存在器械使用时间异常。'
          : '器械使用频率目前仅反映出现时长，尚不能直接判断操作质量或器械使用合理性。',
        '当前报告为 AI 分析内容，结论应作为复盘线索，不能替代术者和上级医师的专业判断。',
      ]
    : ['当前项目未上传视频，无法定位关键问题。']

  const improvementSuggestions = hasVideo
    ? [
        '建议术者在胆囊三角处理阶段持续保持清晰暴露，夹闭或离断前重点复核胆囊管、胆囊动脉及周围组织关系。',
        '建议在牵拉胆囊颈部和分离胆囊床时控制牵拉力度与电凝范围，减少组织撕裂、热损伤和渗血风险。',
        '若术中出现烟雾、镜头污染或视野遮挡，应及时清理镜头并恢复稳定视野后再继续关键操作。',
        '术后复盘时建议重点回看关键步骤时间段，关注夹闭前确认、出血处理、胆囊床分离完整性和器械切换节奏。',
      ]
    : ['请先上传手术视频，再生成完整分析报告。']

  return { summary, metrics, operationAssessment, keyIssues, improvementSuggestions }
}

// 秒 → mm:ss(与本地分析页 formatTimeLabel 一致)
function formatReportDuration(secondsValue) {
  const total = Math.max(0, Math.round(Number(secondsValue) || 0))
  const minutes = Math.floor(total / 60)
  const seconds = total % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

async function submitShare() {
  if (!shareForm.value.title.trim()) {
    shareErrors.value.title = '请填写分享标题'
    showStatus('请先填写必填项：分享标题', 'error')
    return
  }

  const project = projects.value.find((item) => item.id === shareProjectId.value)
  if (!project) return

  shareSubmitting.value = true
  try {
    const existingCommunityId = getSharedCommunityId(project.id)
    const payload = buildSharePayload(project)

    // 第一步:分享/更新元数据
    sharingPhase.value = 'metadata'
    let communityId = existingCommunityId
    if (existingCommunityId) {
      await updateCommunityProject(existingCommunityId, payload)
    } else {
      const data = await shareProject(payload)
      communityId = data.item.id
      setSharedCommunityId(project.id, communityId)
    }

    // 第二步:上传视频(失败不影响元数据分享,提示后重试即可)
    if (shareIncludeVideo.value && project.hasVideo && communityId) {
      sharingPhase.value = 'video'
      try {
        const file = await getProjectVideo(project.id)
        if (file) {
          await uploadProjectVideo(communityId, file, (percent) => {
            shareUploadProgress.value = percent
          })
        }
      } catch (videoError) {
        showStatus(
          `${existingCommunityId ? '分享已更新' : '已分享'}，但视频上传失败：${videoError.message || '请稍后重试'}`,
          'error'
        )
        closeShareModal()
        loadProjects()
        return
      }
    }

    showStatus(existingCommunityId ? '社区分享已更新' : '已分享到社区')
    closeShareModal()
    loadProjects()
  } catch (error) {
    showStatus(error.message || '分享失败，请稍后重试', 'error')
  } finally {
    shareSubmitting.value = false
    sharingPhase.value = ''
  }
}

async function cancelShare(project) {
  const communityId = getSharedCommunityId(project.id)
  if (!communityId) return

  try {
    await deleteCommunityProject(communityId)
    removeSharedProject(project.id)
    showStatus('已取消分享')
    loadProjects()
  } catch (error) {
    showStatus(error.message || '取消分享失败', 'error')
  }
}

onMounted(async () => {
  await syncRunningProjectsPhaseAnalysis()
  loadProjects()
  try {
    categoryGroups.value = (await listCategories()).groups || categoryGroups.value
  } catch {
    // 接口不可用时保留空分组,分享时后端兜底默认分类,不影响主流程
  }
  syncTimer = window.setInterval(async () => {
    await syncRunningProjectsPhaseAnalysis()
    loadProjects()
  }, 5000)
})

onBeforeUnmount(() => {
  if (syncTimer) {
    window.clearInterval(syncTimer)
  }
  if (statusTimer) {
    window.clearTimeout(statusTimer)
  }
})
</script>

<style scoped>
.home-page {
  width: 100%;
  max-width: none;
}
.required-mark {
  color: #dc2626;
  font-weight: 800;
}
.field-error {
  margin-top: 6px;
  color: #dc2626;
  font-size: 12px;
  font-weight: 700;
}
.input-error {
  border-color: #dc2626;
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.12);
}
.top-toast {
  position: fixed;
  top: 84px;
  left: 50%;
  z-index: 9999;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  max-width: min(560px, calc(100vw - 32px));
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 800;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.22);
  transform: translateX(-50%);
}
.top-toast.success {
  background: #ecfdf3;
  color: #166534;
  border: 1px solid #bbf7d0;
}
.top-toast.error {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}
.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.toast-slide-enter-from,
.toast-slide-leave-to {
  opacity: 0;
  transform: translate(-50%, -10px);
}

.entry-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 22px 24px;
  text-align: left;
  font-size: 14px;
  color: #334155;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.entry-card:hover {
  border-color: #93c5fd;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.source-card {
  display: flex;
  align-items: flex-start;
  flex-direction: column;
  gap: 2px;
  padding: 14px 16px;
  text-align: left;
  font-size: 14px;
  color: #334155;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.source-card:hover:not(:disabled) {
  border-color: #94a3b8;
}

.source-card:disabled {
  cursor: not-allowed;
  opacity: 0.75;
}

.source-card-active {
  border-color: #2563eb;
  background: #eff6ff;
}

.subcategory-chip {
  padding: 5px 12px;
  font-size: 13px;
  color: #475569;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 9999px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, color 0.15s;
}

.subcategory-chip:hover {
  border-color: #94a3b8;
}

.subcategory-chip-active {
  color: #1d4ed8;
  background: #eff6ff;
  border-color: #2563eb;
}
</style>
