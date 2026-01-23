import request, { MOCK_MODE } from '@/utils/request'
import { ElMessage } from 'element-plus'

// 模拟用户数据
const mockUsers = [
  { userName: 'admin', realName: '管理员', role: 'admin' },
  { userName: 'user', realName: '普通用户', role: 'user' }
]

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
      message: '导入成功',
      data: {
        batchNo: 'BATCH' + Date.now(),
        totalRows: 100,
        successRows: 95,
        repeatRows: 3,
        invalidRows: 2
      }
    })
  }
  return request.post('/data/import', formData, {
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

    return Promise.resolve({
      code: 200,
      message: '获取成功',
      data: {
        list: pagedRecords,
        total: total
      }
    });
  }
  return request.get('/data/records', { params })
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
    const batchIndex = parseInt(batchNo.replace('BATCH', '')) || 1;
    const errorCount = (batchIndex % 5) + 1; // 1-5个错误
    const errors = errorTemplates.slice(0, errorCount);

    // 导入参数设置
    const importParams = {
      skipDuplicates: true,
      validateFormat: true,
      maxRows: 1000,
      allowedFileTypes: ['.xlsx', '.xls'],
      strictValidation: batchIndex % 3 === 0, // 部分批次启用严格验证
      autoCorrectDates: batchIndex % 2 === 0 // 部分批次启用日期自动修正
    };

    return Promise.resolve({
      code: 200,
      message: '获取成功',
      data: {
        batchNo: batchNo,
        fileName: `${batchNo}_工时数据.xlsx`,
        totalRows: 150 + (batchIndex * 10),
        successRows: 145 + (batchIndex * 10),
        repeatRows: batchIndex % 4,
        invalidRows: batchIndex % 3,
        errors: errors,
        importParams: importParams
      }
    });
  }
  return request.get(`/data/records/${batchNo}`)
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
  return request.get(`/data/records/${batchNo}/report`, {
    responseType: 'blob'
  })
}

// 按批次号查看导入数据
export const getImportDataView = (batchNo, params) => {
  if (MOCK_MODE) {
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
        summary: { totalRecords: 95, totalWorkHours: 760, totalOvertimeHours: 20, userCount: 15, projectCount: 8 }
      }
    })
  }
  return request.get(`/data/records/${batchNo}/data`, { params })
}

// 导出导入数据
export const exportImportData = (batchNo) => {
  if (MOCK_MODE) {
    ElMessage.info('模拟导出导入数据: ' + batchNo)
    return Promise.resolve()
  }
  return request.get(`/data/records/${batchNo}/export`, {
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

// 工时完整性检查（周报提交检查）
export const checkIntegrity = (params) => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '检查完成',
      data: {
        checkNo: 'CHECK' + Date.now(),
        checkResult: {
          totalUsers: 15,
          missingUsers: 3,
          duplicateUsers: 0,
          totalMissingWorkdays: 8,
          totalDuplicateWorkdays: 0
        },
        list: [
          { deptName: '研发部', userName: '张三', issueType: 'missing', gapStartDate: '2026-01-10', gapEndDate: '2026-01-10', affectedWorkdays: 1, description: '缺少工时记录' },
          { deptName: '研发部', userName: '李四', issueType: 'missing', gapStartDate: '2026-01-11', gapEndDate: '2026-01-12', affectedWorkdays: 2, description: '缺少工时记录' },
          { deptName: '研发部', userName: '王五', issueType: 'missing', gapStartDate: '2026-01-14', gapEndDate: '2026-01-15', affectedWorkdays: 2, description: '缺少工时记录' }
        ]
      }
    })
  }
  return request.post('/check/integrity', params)
}

// 工时完整性一致性检查（支持重复检测）
export const checkIntegrityConsistency = (params) => {
  if (MOCK_MODE) {
    const checkNo = 'CHECK' + Date.now()
    return Promise.resolve({
      code: 200,
      message: '检查完成',
      data: {
        checkNo: checkNo,
        summary: {
          totalUsers: 15,
          missingUsers: 2,
          duplicateUsers: 1,
          totalMissingWorkdays: 5,
          totalDuplicateWorkdays: 2,
          integrityRate: 80.0
        },
        list: [
          { deptName: '研发部', userName: '张三', issueType: 'missing', gapStartDate: '2026-01-10', gapEndDate: '2026-01-10', affectedWorkdays: 1, description: '缺少工时记录' },
          { deptName: '研发部', userName: '李四', issueType: 'missing', gapStartDate: '2026-01-11', gapEndDate: '2026-01-12', affectedWorkdays: 2, description: '缺少工时记录' },
          { deptName: '产品部', userName: '王五', issueType: 'duplicate', serialNo: '005', gapStartDate: '2026-01-13', gapEndDate: '2026-01-14', affectedWorkdays: 2, description: '重复提交工时' }
        ]
      }
    })
  }
  return request.post('/check/integrity-consistency', params)
}

// 工时合规性检查（工作时长检查）
export const checkCompliance = (params) => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '检查完成',
      data: {
        checkNo: 'CHECK' + Date.now(),
        checkResult: {
          totalSerials: 25,
          normalSerials: 20,
          shortSerials: 3,
          excessSerials: 2
        },
        list: [
          { deptName: '研发部', userName: '张三', serialNo: '001', startTime: '2026-01-10 09:00:00', endTime: '2026-01-10 16:00:00', totalWorkHours: 7, expectedWorkHours: 8, legalWorkHours: 8, difference: -1, status: 'short' },
          { deptName: '研发部', userName: '李四', serialNo: '002', startTime: '2026-01-11 09:00:00', endTime: '2026-01-11 17:30:00', totalWorkHours: 8.5, expectedWorkHours: 8, legalWorkHours: 8, difference: 0.5, status: 'excess' },
          { deptName: '产品部', userName: '王五', serialNo: '003', startTime: '2026-01-12 09:00:00', endTime: '2026-01-12 15:30:00', totalWorkHours: 6.5, expectedWorkHours: 8, legalWorkHours: 8, difference: -1.5, status: 'short' }
        ]
      }
    })
  }
  return request.post('/check/compliance', params)
}

// 工作时长一致性检查
export const checkWorkHoursConsistency = (params) => {
  if (MOCK_MODE) {
    const checkNo = 'CHECK' + Date.now()
    return Promise.resolve({
      code: 200,
      message: '检查完成',
      data: {
        checkNo: checkNo,
        summary: {
          totalSerials: 30,
          normalSerials: 25,
          shortSerials: 3,
          excessSerials: 2,
          complianceRate: 83.33,
          workTypeStats: {
            project_delivery: { totalHours: 120, avgHours: 8.0 },
            product_research: { totalHours: 80, avgHours: 7.5 },
            presales_support: { totalHours: 24, avgHours: 6.0 },
            dept_internal: { totalHours: 16, avgHours: 4.0 }
          }
        },
        list: [
          { serialNo: '001', userName: '张三', startTime: '2026-01-10 09:00:00', endTime: '2026-01-10 16:00:00', projectDeliveryHours: 6, productResearchHours: 0, presalesSupportHours: 0, deptInternalHours: 0, totalWorkHours: 6, leaveHours: 0, expectedWorkHours: 8, legalWorkHours: 8, difference: -2, status: 'short' },
          { serialNo: '002', userName: '李四', startTime: '2026-01-11 09:00:00', endTime: '2026-01-11 17:30:00', projectDeliveryHours: 7, productResearchHours: 1.5, presalesSupportHours: 0, deptInternalHours: 0, totalWorkHours: 8.5, leaveHours: 0, expectedWorkHours: 8, legalWorkHours: 8, difference: 0.5, status: 'excess' },
          { serialNo: '003', userName: '王五', startTime: '2026-01-12 09:00:00', endTime: '2026-01-12 15:30:00', projectDeliveryHours: 5, productResearchHours: 0, presalesSupportHours: 0, deptInternalHours: 1.5, totalWorkHours: 6.5, leaveHours: 0, expectedWorkHours: 8, legalWorkHours: 8, difference: -1.5, status: 'short' }
        ]
      }
    })
  }
  return request.post('/check/work-hours-consistency', params)
}

// 获取核对历史记录
export const getCheckHistory = (params) => {
  if (MOCK_MODE) {
    const mockRecords = [
      {
        checkNo: 'CHECK20260115001',
        checkType: 'integrity-consistency',
        startDate: '2026-01-10',
        endDate: '2026-01-15',
        deptName: '研发部',
        userName: '',
        checkUser: 'admin',
        checkTime: '2026-01-15 10:30:00',
        triggerType: 'manual',
        checkResult: {
          totalUsers: 15,
          missingUsers: 3,
          duplicateUsers: 0,
          totalMissingWorkdays: 8,
          totalDuplicateWorkdays: 0
        }
      },
      {
        checkNo: 'CHECK20260115002',
        checkType: 'work-hours-consistency',
        startDate: '2026-01-10',
        endDate: '2026-01-15',
        deptName: '',
        userName: '张三',
        checkUser: 'admin',
        checkTime: '2026-01-15 14:20:00',
        triggerType: 'scheduled',
        checkResult: {
          totalSerials: 25,
          normalSerials: 20,
          shortSerials: 3,
          excessSerials: 2
        }
      },
      {
        checkNo: 'CHECK20260114001',
        checkType: 'integrity-consistency',
        startDate: '2026-01-08',
        endDate: '2026-01-12',
        deptName: '产品部',
        userName: '',
        checkUser: 'manager',
        checkTime: '2026-01-14 16:45:00',
        triggerType: 'import',
        checkResult: {
          totalUsers: 10,
          missingUsers: 1,
          duplicateUsers: 1,
          totalMissingWorkdays: 3,
          totalDuplicateWorkdays: 2
        }
      },
      {
        checkNo: 'CHECK20260114002',
        checkType: 'work-hours-consistency',
        startDate: '2026-01-08',
        endDate: '2026-01-12',
        deptName: '设计部',
        userName: '',
        checkUser: 'admin',
        checkTime: '2026-01-14 09:15:00',
        triggerType: 'manual',
        checkResult: {
          totalSerials: 18,
          normalSerials: 15,
          shortSerials: 2,
          excessSerials: 1
        }
      },
      {
        checkNo: 'CHECK20260113001',
        checkType: 'integrity-consistency',
        startDate: '2026-01-06',
        endDate: '2026-01-10',
        deptName: '',
        userName: '李四',
        checkUser: 'admin',
        checkTime: '2026-01-13 11:00:00',
        triggerType: 'scheduled',
        checkResult: {
          totalUsers: 1,
          missingUsers: 0,
          duplicateUsers: 0,
          totalMissingWorkdays: 0,
          totalDuplicateWorkdays: 0
        }
      }
    ]

    const { page = 1, size = 10, checkType, startDate, endDate, checkUser } = params || {}
    let filteredRecords = mockRecords

    // 按核对类型过滤
    if (checkType) {
      filteredRecords = filteredRecords.filter(r => r.checkType === checkType)
    }

    // 按时间范围过滤
    if (startDate && endDate) {
      filteredRecords = filteredRecords.filter(r => {
        return r.startDate >= startDate && r.endDate <= endDate
      })
    }

    // 按执行人过滤
    if (checkUser) {
      filteredRecords = filteredRecords.filter(r => r.checkUser.includes(checkUser))
    }

    const total = filteredRecords.length
    const startIndex = (page - 1) * size
    const endIndex = startIndex + size
    const pagedRecords = filteredRecords.slice(startIndex, endIndex)

    return Promise.resolve({
      code: 200,
      message: '获取成功',
      data: {
        list: pagedRecords,
        total: total
      }
    })
  }
  return request.get('/check/history', { params })
}

// 获取核对详情
export const getCheckDetail = (checkNo) => {
  if (MOCK_MODE) {
    // 根据checkNo模拟不同类型的详情数据
    if (checkNo.includes('integrity')) {
      return Promise.resolve({
        code: 200,
        message: '获取成功',
        data: {
          checkNo: checkNo,
          checkType: 'integrity-consistency',
          startDate: '2026-01-10',
          endDate: '2026-01-15',
          deptName: '研发部',
          userName: '',
          checkUser: 'admin',
          checkTime: '2026-01-15 10:30:00',
          triggerType: 'manual',
          checkResult: {
            totalUsers: 15,
            missingUsers: 3,
            duplicateUsers: 0,
            totalMissingWorkdays: 8,
            totalDuplicateWorkdays: 0
          },
          list: [
            { deptName: '研发部', userName: '张三', issueType: 'missing', gapStartDate: '2026-01-10', gapEndDate: '2026-01-10', affectedWorkdays: 1, description: '缺少工时记录' },
            { deptName: '研发部', userName: '李四', issueType: 'missing', gapStartDate: '2026-01-11', gapEndDate: '2026-01-12', affectedWorkdays: 2, description: '缺少工时记录' },
            { deptName: '研发部', userName: '王五', issueType: 'missing', gapStartDate: '2026-01-14', gapEndDate: '2026-01-15', affectedWorkdays: 2, description: '缺少工时记录' }
          ]
        }
      })
    } else {
      return Promise.resolve({
        code: 200,
        message: '获取成功',
        data: {
          checkNo: checkNo,
          checkType: 'work-hours-consistency',
          startDate: '2026-01-10',
          endDate: '2026-01-15',
          deptName: '',
          userName: '张三',
          checkUser: 'admin',
          checkTime: '2026-01-15 14:20:00',
          triggerType: 'scheduled',
          checkResult: {
            totalSerials: 25,
            normalSerials: 20,
            shortSerials: 3,
            excessSerials: 2
          },
          list: [
            { serialNo: '001', startTime: '2026-01-10 09:00:00', endTime: '2026-01-10 16:00:00', totalWorkHours: 7, expectedWorkHours: 8, legalWorkHours: 8, difference: -1, status: 'short' },
            { serialNo: '002', startTime: '2026-01-11 09:00:00', endTime: '2026-01-11 17:30:00', totalWorkHours: 8.5, expectedWorkHours: 8, legalWorkHours: 8, difference: 0.5, status: 'excess' },
            { serialNo: '003', startTime: '2026-01-12 09:00:00', endTime: '2026-01-12 15:30:00', totalWorkHours: 6.5, expectedWorkHours: 8, legalWorkHours: 8, difference: -1.5, status: 'short' }
          ]
        }
      })
    }
  }
  return request.get(`/check/history/${checkNo}`)
}

// 下载核对报告
export const downloadCheckReport = (checkNo) => {
  if (MOCK_MODE) {
    ElMessage.info('模拟下载报告: ' + checkNo)
    return Promise.resolve()
  }
  return request.get(`/check/history/${checkNo}/report`, {
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
    return Promise.resolve()
  }
  return request.get('/settings/backup', {
    responseType: 'blob'
  })
}

// 数据恢复
export const restoreData = (formData) => {
  if (MOCK_MODE) {
    ElMessage.success('模拟数据恢复成功')
    return Promise.resolve({ code: 200, message: '恢复成功' })
  }
  return request.post('/settings/restore', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// ==================== 节假日管理 ====================

// 获取节假日列表
export const getHolidays = (params) => {
  if (MOCK_MODE) {
    // 模拟节假日数据（包含周末、节假日、调休）
    const mockHolidays = [
      { id: 1, holidayDate: '2026-01-01', holidayName: '元旦', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 2, holidayDate: '2026-01-02', holidayName: '元旦', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 3, holidayDate: '2026-01-03', holidayName: '元旦', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 4, holidayDate: '2026-01-04', holidayName: '周末', year: 2026, isWeekend: 1, isWorkday: 0, dataSource: 'auto', createdAt: '2026-01-01 10:00:00' },
      { id: 5, holidayDate: '2026-01-10', holidayName: '周末', year: 2026, isWeekend: 1, isWorkday: 0, dataSource: 'auto', createdAt: '2026-01-01 10:00:00' },
      { id: 6, holidayDate: '2026-01-11', holidayName: '周末', year: 2026, isWeekend: 1, isWorkday: 0, dataSource: 'auto', createdAt: '2026-01-01 10:00:00' },
      { id: 7, holidayDate: '2026-01-17', holidayName: '周末', year: 2026, isWeekend: 1, isWorkday: 0, dataSource: 'auto', createdAt: '2026-01-01 10:00:00' },
      { id: 8, holidayDate: '2026-01-18', holidayName: '周末', year: 2026, isWeekend: 1, isWorkday: 0, dataSource: 'auto', createdAt: '2026-01-01 10:00:00' },
      { id: 9, holidayDate: '2026-01-24', holidayName: '周末', year: 2026, isWeekend: 1, isWorkday: 0, dataSource: 'auto', createdAt: '2026-01-01 10:00:00' },
      { id: 10, holidayDate: '2026-01-25', holidayName: '周末', year: 2026, isWeekend: 1, isWorkday: 0, dataSource: 'auto', createdAt: '2026-01-01 10:00:00' },
      { id: 11, holidayDate: '2026-02-10', holidayName: '春节', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 12, holidayDate: '2026-02-11', holidayName: '春节', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 13, holidayDate: '2026-02-12', holidayName: '春节', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 14, holidayDate: '2026-02-13', holidayName: '春节', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 15, holidayDate: '2026-02-14', holidayName: '春节', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 16, holidayDate: '2026-02-15', holidayName: '春节', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 17, holidayDate: '2026-02-16', holidayName: '春节', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 18, holidayDate: '2026-02-07', holidayName: '春节调休', year: 2026, isWeekend: 0, isWorkday: 1, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 19, holidayDate: '2026-04-04', holidayName: '清明节', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 20, holidayDate: '2026-04-05', holidayName: '清明节', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 21, holidayDate: '2026-04-06', holidayName: '清明节', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 22, holidayDate: '2026-05-01', holidayName: '劳动节', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 23, holidayDate: '2026-05-02', holidayName: '劳动节', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 24, holidayDate: '2026-05-03', holidayName: '劳动节', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 25, holidayDate: '2026-05-04', holidayName: '劳动节', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
      { id: 26, holidayDate: '2026-05-05', holidayName: '劳动节', year: 2026, isWeekend: 0, isWorkday: 0, dataSource: 'api', createdAt: '2026-01-01 10:00:00' },
    ]

    const { page = 1, size = 20, year, dataSource } = params || {}
    let filteredHolidays = mockHolidays

    // 按年份过滤
    if (year) {
      filteredHolidays = filteredHolidays.filter(h => h.year === parseInt(year))
    }

    // 按数据来源过滤
    if (dataSource) {
      filteredHolidays = filteredHolidays.filter(h => h.dataSource === dataSource)
    }

    const total = filteredHolidays.length
    const startIndex = (page - 1) * size
    const endIndex = startIndex + size
    const pagedHolidays = filteredHolidays.slice(startIndex, endIndex)

    return Promise.resolve({
      code: 200,
      message: '获取成功',
      data: {
        list: pagedHolidays,
        total: total
      }
    })
  }
  return request.get('/holidays', { params })
}

// 添加节假日
export const addHoliday = (data) => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '添加成功',
      data: {
        id: Date.now(),
        ...data,
        year: new Date(data.holidayDate).getFullYear(),
        dataSource: 'manual',
        createdAt: new Date().toLocaleString('zh-CN')
      }
    })
  }
  return request.post('/holidays', data)
}

// 删除节假日
export const deleteHoliday = (id) => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '删除成功'
    })
  }
  return request.delete(`/holidays/${id}`)
}

// 批量导入节假日
export const batchImportHolidays = (data) => {
  if (MOCK_MODE) {
    const holidays = data.holidays || []
    const successCount = holidays.length
    const skipCount = 0

    return Promise.resolve({
      code: 200,
      message: '导入完成',
      data: {
        successCount,
        skipCount
      }
    })
  }
  return request.post('/holidays/batch', data)
}

// API同步节假日
export const syncHolidays = (year) => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '同步成功',
      data: {
        year: year,
        total: 15,
        successCount: 15,
        dataSource: 'api'
      }
    })
  }
  return request.post(`/holidays/sync/${year}`)
}

// 生成周末数据
export const generateWeekends = (year) => {
  if (MOCK_MODE) {
    return Promise.resolve({
      code: 200,
      message: '生成成功',
      data: {
        year: year,
        total: 104,
        generatedCount: 104,
        dataSource: 'auto'
      }
    })
  }
  return request.post(`/holidays/generate-weekends/${year}`)
}

// 计算工作日
export const calculateWorkdays = (data) => {
  if (MOCK_MODE) {
    const { startDate, endDate } = data
    const start = new Date(startDate)
    const end = new Date(endDate)
    const diffTime = Math.abs(end - start)
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1
    const workdays = Math.floor(diffDays * 5 / 7)

    return Promise.resolve({
      code: 200,
      message: '计算成功',
      data: {
        totalDays: diffDays,
        workdays: workdays,
        weekendDays: diffDays - workdays,
        holidays: 5,
        workdayDates: [] // 模拟空数组
      }
    })
  }
  return request.post('/holidays/calculate-workdays', data)
}
