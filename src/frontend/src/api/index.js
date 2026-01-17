import request, { MOCK_MODE } from '@/utils/request'
import { ElMessage } from 'element-plus'

// 模拟用户数据
const mockUsers = [
  { userName: 'admin', realName: '管理员', role: 'admin' },
  { userName: 'user', realName: '普通用户', role: 'user' }
]

// 生成批次号辅助函数（与API设计文档一致）
const generateBatchNo = () => {
  const now = new Date()
  const timestamp = now.toISOString().replace(/[-:T.]/g, '').slice(0, 14) // YYYYMMDDHHMMSS
  const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0')
  return `IMP_${timestamp}_${random}`
}

const generateCheckNo = () => {
  const now = new Date()
  const timestamp = now.toISOString().replace(/[-:T.]/g, '').slice(0, 14) // YYYYMMDDHHMMSS
  const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0')
  return `CHK_${timestamp}_${random}`
}

// 模拟数据字典
const mockDataDict = {
  projects: ['智慧城市平台', '企业管理系统', '移动应用开发', '数据分析平台'],
  departments: ['研发部', '产品部', '设计部', '运营部'],
  users: [
    { userName: '张三', deptName: '研发部' },
    { userName: '李四', deptName: '产品部' },
    { userName: '王五', deptName: '设计部' },
    { userName: '赵六', deptName: '运营部' }
  ]
}

// 用户登录
export const login = (data) => {
  if (MOCK_MODE) {
    // 模拟登录
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const { username, password } = data
        if (!username || password.length < 6) {
          reject(new Error('用户名或密码错误'))
          return
        }
        const user = mockUsers.find(u => u.userName === username) || { userName: username, realName: username, role: 'user' }
        resolve({
          code: 200,
          message: '登录成功',
          data: {
            token: 'mock-token-' + Date.now(),
            userInfo: user
          }
        })
        ElMessage.success('登录成功（模拟模式）')
      }, 500)
    })
  }
  return request.post('/auth/login', data)
}

// Excel 数据导入
export const importExcel = (formData) => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '导入完成',
      data: {
        batchNo: generateBatchNo(),
        totalRows: 100,
        successRows: 95,
        repeatRows: 3,
        invalidRows: 2,
        errors: [
          { row: 5, field: '开始时间', error: '时间格式错误，应为YYYY-MM-DD HH:mm:ss' },
          { row: 12, field: '工作时长', error: '工作时长为负数' }
        ]
      }
    })
  }
  return request.post('/import/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 获取导入记录列表
export const getImportRecords = (params) => {
  if (MOCK_MODE) {
    // 模拟导入记录数据
    const mockRecords = [
      { batchNo: 'BATCH001', fileName: '研发部_2025年9月工时.xlsx', totalRows: 150, successRows: 145, repeatRows: 3, invalidRows: 2, importTime: '2025-09-15 10:30:00', importUser: 'admin' },
      { batchNo: 'BATCH002', fileName: '产品部_2025年9月工时.xlsx', totalRows: 120, successRows: 118, repeatRows: 1, invalidRows: 1, importTime: '2025-09-18 14:20:00', importUser: 'manager' },
      { batchNo: 'BATCH003', fileName: '智慧城市平台_Q3工时.xlsx', totalRows: 200, successRows: 195, repeatRows: 4, invalidRows: 1, importTime: '2025-10-08 09:45:00', importUser: 'admin' },
      { batchNo: 'BATCH004', fileName: '企业管理系统_10月工时.xlsx', totalRows: 180, successRows: 175, repeatRows: 3, invalidRows: 2, importTime: '2025-10-15 11:10:00', importUser: 'user1' },
      { batchNo: 'BATCH005', fileName: '研发部_2025年10月工时.xlsx', totalRows: 160, successRows: 158, repeatRows: 1, invalidRows: 1, importTime: '2025-10-22 16:30:00', importUser: 'admin' },
      { batchNo: 'BATCH006', fileName: '2025年11月工时统计.xlsx', totalRows: 300, successRows: 292, repeatRows: 5, invalidRows: 3, importTime: '2025-11-05 10:15:00', importUser: 'admin' },
      { batchNo: 'BATCH007', fileName: '移动应用开发_11月工时.xlsx', totalRows: 220, successRows: 215, repeatRows: 3, invalidRows: 2, importTime: '2025-11-12 13:45:00', importUser: 'manager' },
      { batchNo: 'BATCH008', fileName: '设计部_2025年11月工时.xlsx', totalRows: 130, successRows: 128, repeatRows: 1, invalidRows: 1, importTime: '2025-11-19 15:20:00', importUser: 'user2' },
      { batchNo: 'BATCH009', fileName: '数据分析平台_Q4工时.xlsx', totalRows: 250, successRows: 245, repeatRows: 3, invalidRows: 2, importTime: '2025-12-03 09:30:00', importUser: 'admin' },
      { batchNo: 'BATCH010', fileName: '全公司_2025年12月工时汇总.xlsx', totalRows: 500, successRows: 490, repeatRows: 7, invalidRows: 3, importTime: '2025-12-10 14:50:00', importUser: 'admin' },
      { batchNo: 'BATCH011', fileName: '运营部_2025年12月工时.xlsx', totalRows: 140, successRows: 138, repeatRows: 1, invalidRows: 1, importTime: '2025-12-17 11:25:00', importUser: 'user1' },
      { batchNo: 'BATCH012', fileName: '2026年1月工时数据.xlsx', totalRows: 180, successRows: 177, repeatRows: 2, invalidRows: 1, importTime: '2026-01-05 10:00:00', importUser: 'admin' },
      { batchNo: 'BATCH013', fileName: '项目A_2026年1月工时.xlsx', totalRows: 110, successRows: 108, repeatRows: 1, invalidRows: 1, importTime: '2026-01-12 13:15:00', importUser: 'manager' },
      { batchNo: 'BATCH014', fileName: '研发部_2026年1月工时.xlsx', totalRows: 170, successRows: 168, repeatRows: 1, invalidRows: 1, importTime: '2026-01-19 16:40:00', importUser: 'admin' }
    ];

    // 模拟分页逻辑
    const { page = 1, size = 20, fileName = '', startDate = '', endDate = '' } = params || {};

    // 过滤数据
    let filteredRecords = mockRecords;

    // 按文件名过滤
    if (fileName) {
      filteredRecords = filteredRecords.filter(record =>
        record.fileName.toLowerCase().includes(fileName.toLowerCase())
      );
    }

    // 按时间范围过滤
    if (startDate && endDate) {
      filteredRecords = filteredRecords.filter(record => {
        const recordDate = new Date(record.importTime.split(' ')[0]);
        const start = new Date(startDate);
        const end = new Date(endDate);
        return recordDate >= start && recordDate <= end;
      });
    }

    // 计算分页
    const total = filteredRecords.length;
    const startIndex = (page - 1) * size;
    const endIndex = startIndex + size;
    const pagedRecords = filteredRecords.slice(startIndex, endIndex);
    const totalPages = Math.ceil(total / size);

    return Promise.resolve({
      code: 200,
      message: '获取成功',
      data: {
        list: pagedRecords,
        total: total,
        page: page,
        size: size,
        totalPages: totalPages
      }
    });
  }
  return request.get('/import/records', { params })
}

// 获取导入批次详情
export const getImportDetail = (batchNo) => {
  if (MOCK_MODE) {
    // 根据批次号生成错误详情
    const errorTemplates = [
      { row: 12, field: '开始时间', error: '时间格式错误，应为YYYY-MM-DD HH:mm:ss' },
      { row: 25, field: '工作时长', error: '工作时长超过168小时（一周最大时长）' },
      { row: 38, field: '结束时间', error: '结束时间早于开始时间' },
      { row: 47, field: '项目名称', error: '项目名称不能为空' },
      { row: 52, field: '审批状态', error: '审批状态必须为"通过"或"驳回"' },
      { row: 65, field: '加班时长', error: '加班时长应为数字类型' },
      { row: 78, field: '部门名称', error: '部门名称不在允许列表中' },
      { row: 83, field: '工作内容', error: '工作内容超过最大长度限制' }
    ];

    // 为不同批次生成不同数量的错误
    const batchIndex = parseInt(batchNo.replace(/\D/g, '')) || 1;
    const errorCount = (batchIndex % 5) + 1; // 1-5个错误
    const errors = errorTemplates.slice(0, errorCount);

    const successRows = 145 + (batchIndex * 10);
    const repeatRows = batchIndex % 4;
    const invalidRows = batchIndex % 3;

    return Promise.resolve({
      code: 200,
      message: '获取成功',
      data: {
        batchNo: batchNo,
        fileName: `${batchNo}_工时数据.xlsx`,
        fileSize: 102400,
        totalRows: 150 + (batchIndex * 10),
        successRows: successRows,
        repeatRows: repeatRows,
        invalidRows: invalidRows,
        duplicateStrategy: 'skip',
        importUser: 'admin',
        importTime: '2026-01-15T10:30:00+08:00',
        errors: errors,
        summary: {
          totalWorkHours: successRows * 8,
          totalOvertimeHours: Math.floor(successRows * 0.2),
          userCount: 15,
          projectCount: 8
        }
      }
    });
  }
  return request.get(`/import/record/${batchNo}`)
}

// 下载原始文件
export const downloadImportReport = (batchNo) => {
  if (MOCK_MODE) {
    ElMessage.info('模拟下载文件: ' + batchNo)

    // 生成模拟的Excel文件内容（CSV格式，可以用Excel打开）
    // 创建CSV文件内容
    const headers = ['序号', '姓名', '部门', '项目名称', '开始时间', '结束时间', '工作时长', '加班时长', '工作内容', '审批结果', '审批状态'];

    // 生成5行模拟数据
    const dataRows = [];
    for (let i = 1; i <= 5; i++) {
      dataRows.push([
        `00${i}`,
        `用户${i}`,
        i % 2 === 0 ? '研发部' : '产品部',
        `项目${i}`,
        `2026-01-${String(i).padStart(2, '0')} 09:00:00`,
        `2026-01-${String(i).padStart(2, '0')} 18:00:00`,
        '8',
        i % 3 === 0 ? '1' : '0',
        `工作内容示例${i}`,
        '通过',
        '已完成'
      ]);
    }

    // 组合CSV内容
    const csvContent = [
      headers.join(','),
      ...dataRows.map(row => row.join(','))
    ].join('\n');

    // 添加UTF-8 BOM以便Excel正确识别中文
    const bom = '\uFEFF';
    const fullContent = bom + csvContent;

    // 转换为Blob
    const blob = new Blob([fullContent], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

    // 返回Blob，前端会将其作为Excel文件下载
    return Promise.resolve(blob);
  }
  return request.get(`/import/record/${batchNo}/report`, {
    responseType: 'blob'
  })
}

// 按批次号查看导入数据
export const getImportDataView = (batchNo, params) => {
  if (MOCK_MODE) {
    const { page = 1, size = 20 } = params || {};
    const totalPages = 5;

    return Promise.resolve({
      code: 200,
      message: '获取成功',
      data: {
        list: [
          { serialNo: '001', userName: '张三', projectName: '智慧城市平台', projectManager: '李经理', startTime: '2026-01-15 09:00:00', endTime: '2026-01-15 18:00:00', workHours: 8, overtimeHours: 0, deptName: '研发部', workContent: '开发功能模块', approvalResult: '通过', approvalStatus: '已完成' },
          { serialNo: '002', userName: '李四', projectName: '智慧城市平台', projectManager: '李经理', startTime: '2026-01-15 09:00:00', endTime: '2026-01-15 19:00:00', workHours: 8, overtimeHours: 1, deptName: '研发部', workContent: '代码审查', approvalResult: '通过', approvalStatus: '已完成' },
          { serialNo: '003', userName: '王五', projectName: '企业管理系统', projectManager: '王经理', startTime: '2026-01-14 09:30:00', endTime: '2026-01-14 17:30:00', workHours: 7, overtimeHours: 0, deptName: '设计部', workContent: 'UI设计', approvalResult: '通过', approvalStatus: '已完成' },
          { serialNo: '004', userName: '赵六', projectName: '移动应用开发', projectManager: '张经理', startTime: '2026-01-14 10:00:00', endTime: '2026-01-14 18:00:00', workHours: 7.5, overtimeHours: 0, deptName: '运营部', workContent: '产品测试', approvalResult: '通过', approvalStatus: '已完成' },
          { serialNo: '005', userName: '张三', projectName: '数据分析平台', projectManager: '刘经理', startTime: '2026-01-13 09:00:00', endTime: '2026-01-13 18:30:00', workHours: 8.5, overtimeHours: 0.5, deptName: '研发部', workContent: '数据建模', approvalResult: '通过', approvalStatus: '已完成' }
        ],
        total: 95,
        page: page,
        size: size,
        totalPages: totalPages,
        summary: { totalRecords: 95, totalWorkHours: 760, totalOvertimeHours: 20, userCount: 15, projectCount: 8 }
      }
    })
  }
  return request.get(`/import/record/${batchNo}/data`, { params })
}

// 导出导入数据
export const exportImportData = (batchNo) => {
  if (MOCK_MODE) {
    ElMessage.info('模拟导出导入数据: ' + batchNo)
    return Promise.resolve()
  }
  return request.get(`/import/record/${batchNo}/export`, {
    responseType: 'blob'
  })
}

// 项目维度查询
export const queryByProject = (params) => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '查询成功',
      data: {
        list: [
          { serialNo: '001', userName: '张三', projectName: '智慧城市平台', projectManager: '李经理', startTime: '2026-01-15 09:00:00', endTime: '2026-01-15 18:00:00', workHours: 8, overtimeHours: 0, deptName: '研发部', workContent: '开发功能模块' },
          { serialNo: '002', userName: '李四', projectName: '智慧城市平台', projectManager: '李经理', startTime: '2026-01-15 09:00:00', endTime: '2026-01-15 19:00:00', workHours: 8, overtimeHours: 1, deptName: '研发部', workContent: '代码审查' }
        ],
        total: 2,
        summary: { totalWorkHours: 16, totalOvertimeHours: 1, projectCount: 1, userCount: 2 }
      }
    })
  }
  return request.get('/query/project', { params })
}

// 组织维度查询
export const queryByOrganization = (params) => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '查询成功',
      data: {
        list: [
          { serialNo: '001', userName: '张三', projectName: '智慧城市平台', projectManager: '李经理', startTime: '2026-01-15 09:00:00', endTime: '2026-01-15 18:00:00', workHours: 8, overtimeHours: 0, deptName: '研发部', workContent: '开发功能模块' },
          { serialNo: '003', userName: '王五', projectName: '企业管理系统', projectManager: '王经理', startTime: '2026-01-15 09:30:00', endTime: '2026-01-15 17:30:00', workHours: 7, overtimeHours: 0, deptName: '设计部', workContent: 'UI设计' }
        ],
        total: 2,
        summary: { totalWorkHours: 15, totalOvertimeHours: 0, deptCount: 2, userCount: 2 }
      }
    })
  }
  return request.get('/query/organization', { params })
}

// 导出查询结果
export const exportQueryResult = (params) => {
  if (MOCK_MODE) {
    ElMessage.info('模拟导出查询结果')
    return Promise.resolve()
  }
  return request.post('/query/export', params, {
    responseType: 'blob'
  })
}

// 工时完整性检查
export const checkIntegrity = (params) => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '核对完成',
      data: {
        checkNo: generateCheckNo(),
        summary: {
          totalUsers: 50,
          missingUsers: 3,
          totalMissingDays: 15,
          integrityRate: 99.5
        },
        list: [
          {
            deptName: '研发部',
            userName: '张三',
            missingDates: '2026-01-10,2026-01-11,2026-01-15',
            missingDays: 3,
            lastSubmitDate: '2026-01-14'
          },
          {
            deptName: '产品部',
            userName: '李四',
            missingDates: '2026-01-12',
            missingDays: 1,
            lastSubmitDate: '2026-01-13'
          },
          {
            deptName: '设计部',
            userName: '王五',
            missingDates: '2026-01-08,2026-01-09,2026-01-10,2026-01-11,2026-01-12',
            missingDays: 5,
            lastSubmitDate: '2026-01-07'
          }
        ]
      }
    })
  }
  return request.post('/check/integrity', params)
}

// 工时合规性检查
export const checkCompliance = (params) => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '核对完成',
      data: {
        checkNo: generateCheckNo(),
        summary: {
          totalRecords: 1000,
          abnormalRecords: 15,
          abnormalUsers: 5,
          complianceRate: 98.5,
          invalidTypes: {
            shortHours: 8,
            excessOvertime: 5,
            cumulativeExcess: 2
          }
        },
        list: [
          {
            deptName: '研发部',
            userName: '张三',
            date: '2026-01-15',
            workHours: 3.0,
            overtimeHours: 0.0,
            abnormalType: 'shortHours',
            abnormalDesc: '工作时长3小时，低于下限4小时'
          },
          {
            deptName: '产品部',
            userName: '李四',
            date: '2026-01-15',
            workHours: 8.0,
            overtimeHours: 5.0,
            abnormalType: 'excessOvertime',
            abnormalDesc: '加班时长5小时，超过上限4小时'
          },
          {
            deptName: '设计部',
            userName: '王五',
            date: '2026-01-14',
            workHours: 8.0,
            overtimeHours: 0.0,
            abnormalType: 'shortHours',
            abnormalDesc: '工作时长2小时，低于下限4小时'
          }
        ]
      }
    })
  }
  return request.post('/check/compliance', params)
}

// 获取核对历史记录
export const getCheckHistory = (params) => {
  if (MOCK_MODE) {
    const { page = 1, size = 20 } = params || {};
    const totalPages = 1;

    return Promise.resolve({
      code: 200,
      message: '获取成功',
      data: {
        list: [
          {
            id: 1,
            checkNo: 'CHK_20260115100000_0001',
            checkType: 'integrity',
            checkTypeName: '完整性检查',
            startDate: '2026-01-01',
            endDate: '2026-01-31',
            deptName: '研发部',
            userName: null,
            checkResult: {
              totalUsers: 50,
              missingUsers: 3,
              totalMissingDays: 15,
              integrityRate: 99.5
            },
            checkUser: 'admin',
            checkTime: '2026-01-15T10:00:00+08:00'
          },
          {
            id: 2,
            checkNo: 'CHK_20260114160000_0002',
            checkType: 'compliance',
            checkTypeName: '合规性检查',
            startDate: '2026-01-01',
            endDate: '2026-01-31',
            deptName: null,
            userName: null,
            checkResult: {
              totalRecords: 1000,
              abnormalRecords: 15,
              abnormalUsers: 5,
              complianceRate: 98.5,
              invalidTypes: {
                shortHours: 8,
                excessOvertime: 5,
                cumulativeExcess: 2
              }
            },
            checkUser: 'admin',
            checkTime: '2026-01-14T16:00:00+08:00'
          },
          {
            id: 3,
            checkNo: 'CHK_20260113093000_0003',
            checkType: 'integrity',
            checkTypeName: '完整性检查',
            startDate: '2026-01-01',
            endDate: '2026-01-15',
            deptName: '产品部',
            userName: '李四',
            checkResult: {
              totalUsers: 10,
              missingUsers: 1,
              totalMissingDays: 3,
              integrityRate: 99.0
            },
            checkUser: 'admin',
            checkTime: '2026-01-13T09:30:00+08:00'
          }
        ],
        total: 3,
        page: page,
        size: size,
        totalPages: totalPages
      }
    })
  }
  return request.get('/check/history', { params })
}

// 获取核对详情
export const getCheckDetail = (checkNo) => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '获取成功',
      data: { checkNo: checkNo, checkType: '完整性检查', details: [] }
    })
  }
  return request.get(`/check/record/${checkNo}`)
}

// 下载核对报告
export const downloadCheckReport = (checkNo) => {
  if (MOCK_MODE) {
    ElMessage.info('模拟下载报告: ' + checkNo)
    return Promise.resolve()
  }
  return request.get(`/check/record/${checkNo}/report`, {
    responseType: 'blob'
  })
}

// 获取数据字典（项目名称、部门名称等）
export const getDataDict = () => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '获取成功',
      data: mockDataDict
    })
  }
  return request.get('/data/dict')
}

// 数据备份
export const backupData = () => {
  if (MOCK_MODE) {
    ElMessage.info('模拟数据备份')
    // 模拟返回一个空blob
    return Promise.resolve(new Blob(['mock backup data'], { type: 'application/x-sqlite3' }))
  }
  return request.post('/system/backup', {}, {
    responseType: 'blob'
  })
}

// 数据恢复
export const restoreData = (formData) => {
  if (MOCK_MODE) {
    ElMessage.success('模拟数据恢复成功')
    return Promise.resolve({ code: 200, message: '恢复成功' })
  }
  return request.post('/system/restore', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 获取系统配置
export const getSystemConfig = (params) => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '获取成功',
      data: {
        import: [
          { configKey: 'import.max_file_size', configValue: '10', configType: 'number', category: 'import', description: '单次导入最大文件大小(MB)', isEditable: true },
          { configKey: 'import.max_rows', configValue: '1000', configType: 'number', category: 'import', description: '单次导入最大行数', isEditable: true },
          { configKey: 'import.duplicate_strategy', configValue: 'skip', configType: 'string', category: 'import', description: '重复数据处理策略(skip/cover)', isEditable: true }
        ],
        check: [
          { configKey: 'check.standard_hours', configValue: '8', configType: 'number', category: 'check', description: '标准工作时长(小时)', isEditable: true },
          { configKey: 'check.min_hours', configValue: '4', configType: 'number', category: 'check', description: '最小工作时长(小时)', isEditable: true },
          { configKey: 'check.max_overtime', configValue: '4', configType: 'number', category: 'check', description: '单日最大加班时长(小时)', isEditable: true },
          { configKey: 'check.max_monthly_overtime', configValue: '80', configType: 'number', category: 'check', description: '月度最大加班时长(小时)', isEditable: true },
          { configKey: 'check.workdays', configValue: '[1,2,3,4,5]', configType: 'json', category: 'check', description: '标准工作日(1-7,周一到周日)', isEditable: true }
        ]
      }
    })
  }
  return request.get('/system/config', { params })
}

// 更新系统配置
export const updateSystemConfig = (data) => {
  if (MOCK_MODE) {
    ElMessage.success('配置更新成功')
    return Promise.resolve({ code: 200, message: '配置更新成功' })
  }
  return request.put('/system/config', data)
}

// 获取备份文件列表
export const getBackupList = () => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '获取成功',
      data: [
        { filename: 'backup_20260115_103000.db', fileSize: 102400, createTime: '2026-01-15T10:30:00' },
        { filename: 'backup_20260114_150000.db', fileSize: 101500, createTime: '2026-01-14T15:00:00' },
        { filename: 'backup_20260113_093000.db', fileSize: 100800, createTime: '2026-01-13T09:30:00' }
      ]
    })
  }
  return request.get('/system/backups')
}

// 获取系统信息
export const getSystemInfo = () => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '获取成功',
      data: {
        dbSize: 102400,
        totalRecords: 1000,
        totalImports: 50,
        totalUsers: 10,
        latestImportTime: '2026-01-15T10:30:00',
        backupCount: 3,
        systemVersion: '1.0.0'
      }
    })
  }
  return request.get('/system/info')
}
