'use client';

import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Card, 
  List, 
  Tag, 
  Space, 
  Button, 
  Input, 
  Spin, 
  Empty, 
  Modal, 
  InputNumber, 
  Divider, 
  Tooltip, 
  App,
  Badge,
  Table,
  Drawer,
  Form,
  Select,
  Radio
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  CopyOutlined, 
  SearchOutlined,
  TagsOutlined,
  FileTextOutlined,
  ReloadOutlined,
  StarOutlined,
  StarFilled,
  EyeOutlined
} from '@ant-design/icons';
import AppLayout from '../../components/layout/AppLayout';
import { fetchAllScripts, generateScripts } from '../../services/api';
import type { ScriptGroup, Script } from '../../types';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Search } = Input;
const { Option } = Select;

const ScriptsPage = () => {
  const { message, modal } = App.useApp();
  const [loading, setLoading] = useState<boolean>(true);
  const [scriptGroups, setScriptGroups] = useState<ScriptGroup[]>([]);
  const [searchText, setSearchText] = useState<string>('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [allTags, setAllTags] = useState<string[]>([]);
  const [generatingScripts, setGeneratingScripts] = useState<boolean>(false);
  const [currentJobId, setCurrentJobId] = useState<string>('');
  const [numScripts, setNumScripts] = useState<number>(3);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  
  // 详情抽屉相关状态
  const [detailsVisible, setDetailsVisible] = useState<boolean>(false);
  const [currentGroup, setCurrentGroup] = useState<ScriptGroup | null>(null);
  const [editableOriginalText, setEditableOriginalText] = useState<string>('');
  const [editingOriginalText, setEditingOriginalText] = useState<boolean>(false);
  
  // 生成脚本相关状态
  const [generateDrawerVisible, setGenerateDrawerVisible] = useState<boolean>(false);
  const [customPrompt, setCustomPrompt] = useState<string>('');
  const [overwriteScripts, setOverwriteScripts] = useState<boolean>(false);
  const [defaultPrompt, setDefaultPrompt] = useState<string>(`你是一位专业的直播内容创作者，请根据以下文本内容和标签，生成{num_scripts}个不同风格的直播脚本。

原始文本：
{text}

标签：{tags}

要求：
1. 生成{num_scripts}个不同的脚本，每个脚本风格各异
2. 保持原始文本的核心信息和主要观点
3. 使用更加生动、吸引人的表达方式
4. 增加一些互动元素或号召性用语
5. 使用口语化的语言，增加亲和力
6. 每个脚本用"---"分隔

请直接输出创作后的内容，不要包含解释：`);

  // 加载脚本数据
  const loadScriptData = async () => {
    try {
      setLoading(true);
      // 使用新的API函数获取所有脚本
      const scriptGroupsData = await fetchAllScripts();
      
      setScriptGroups(scriptGroupsData);
      
      // 收集所有标签
      const tagsSet = new Set<string>();
      scriptGroupsData.forEach(group => {
        if (group.tags) {
          group.tags.forEach(tag => tagsSet.add(tag));
        }
      });
      setAllTags(Array.from(tagsSet));
      
      // 从本地存储加载收藏
      const savedFavorites = localStorage.getItem('scriptFavorites');
      if (savedFavorites) {
        setFavorites(new Set(JSON.parse(savedFavorites)));
      }
      
    } catch (error) {
      console.error('加载脚本数据失败:', error);
      message.error('加载脚本数据失败，请稍后再试');
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    loadScriptData();
  }, []);

  // 保存收藏到本地存储
  useEffect(() => {
    localStorage.setItem('scriptFavorites', JSON.stringify(Array.from(favorites)));
  }, [favorites]);

  // 切换收藏状态
  const toggleFavorite = (scriptId: string) => {
    const newFavorites = new Set(favorites);
    if (newFavorites.has(scriptId)) {
      newFavorites.delete(scriptId);
    } else {
      newFavorites.add(scriptId);
    }
    setFavorites(newFavorites);
  };

  // 打开详情抽屉
  const showDetails = (group: ScriptGroup) => {
    setCurrentGroup(group);
    setEditableOriginalText(group.original_text);
    setDetailsVisible(true);
  };

  // 关闭详情抽屉
  const closeDetails = () => {
    setDetailsVisible(false);
    setCurrentGroup(null);
    setEditingOriginalText(false);
  };

  // 保存编辑后的原文
  const saveOriginalText = () => {
    if (!currentGroup) return;
    
    // 这里应该调用API保存修改后的原文
    // 暂时只在前端更新
    const updatedGroups = scriptGroups.map(group => {
      if (group.job_id === currentGroup.job_id) {
        return { ...group, original_text: editableOriginalText };
      }
      return group;
    });
    
    setScriptGroups(updatedGroups);
    setCurrentGroup({ ...currentGroup, original_text: editableOriginalText });
    setEditingOriginalText(false);
    message.success('原文已更新');
  };

  // 处理生成更多脚本
  const handleGenerateMoreScripts = async () => {
    if (!currentJobId) return;
    
    try {
      setGeneratingScripts(true);
      
      // 发送请求
      await generateScripts(currentJobId, numScripts, customPrompt, overwriteScripts);
      
      // 立即显示成功消息并关闭抽屉
      message.success('脚本生成任务已提交，请稍后刷新页面查看');
      setGenerateDrawerVisible(false);
      // 确保详情抽屉也关闭
      setDetailsVisible(false);
      
      // 设置一个短暂的延迟后刷新脚本数据
      setTimeout(() => {
        loadScriptData();
      }, 1000);
    } catch (error) {
      console.error('生成脚本失败:', error);
      message.error('生成脚本失败，请稍后再试');
    } finally {
      // 无论成功或失败，都结束加载状态
      setGeneratingScripts(false);
    }
  };

  // 复制脚本内容
  const copyScript = (content: string) => {
    navigator.clipboard.writeText(content)
      .then(() => message.success('已复制到剪贴板'))
      .catch(() => message.error('复制失败，请手动复制'));
  };

  // 筛选脚本
  const filteredScriptGroups = scriptGroups.filter(group => {
    // 搜索文本过滤
    const textMatch = searchText === '' || 
      group.original_text.toLowerCase().includes(searchText.toLowerCase()) ||
      group.scripts.some(script => script.content.toLowerCase().includes(searchText.toLowerCase()));
    
    // 标签过滤
    const tagMatch = selectedTags.length === 0 || 
      selectedTags.every(tag => group.tags?.includes(tag));
    
    return textMatch && tagMatch;
  });

  // 打开生成更多脚本的抽屉
  const showGenerateScriptsDrawer = (jobId: string) => {
    setCurrentJobId(jobId);
    setCustomPrompt(defaultPrompt);
    setGenerateDrawerVisible(true);
    // 关闭详情抽屉
    setDetailsVisible(false);
  };

  // 表格列定义
  const columns = [
    {
      title: '原文摘要',
      dataIndex: 'original_text',
      key: 'original_text',
      render: (text: string) => (
        <Tooltip title={text}>
          <Text ellipsis style={{ maxWidth: 300 }}>
            {text.length > 50 ? `${text.substring(0, 50)}...` : text}
          </Text>
        </Tooltip>
      ),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => (
        <Space wrap>
          {tags?.map(tag => (
            <Tag key={tag} color="blue">
              {tag}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '脚本数量',
      dataIndex: 'scripts',
      key: 'scripts_count',
      render: (scripts: Script[]) => <Badge count={scripts.length} style={{ backgroundColor: '#52c41a' }} />,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: ScriptGroup) => (
        <Space>
          <Button 
            type="primary" 
            icon={<EyeOutlined />} 
            onClick={() => showDetails(record)}
          >
            查看详情
          </Button>
          <Button
            icon={<PlusOutlined />}
            onClick={() => showGenerateScriptsDrawer(record.job_id)}
          >
            生成更多
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <AppLayout>
      <App>
        <div style={{ padding: '0 0 24px 0' }}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Title level={2} style={{ margin: 0 }}>脚本列表</Title>
              <Button 
                type="primary" 
                icon={<ReloadOutlined />} 
                onClick={loadScriptData}
                loading={loading}
              >
                刷新
              </Button>
            </div>

            <Card>
              <Space direction="vertical" style={{ width: '100%' }}>
                <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
                  <Search
                    placeholder="搜索脚本内容或原文"
                    allowClear
                    enterButton={<SearchOutlined />}
                    onSearch={(value) => setSearchText(value)}
                    style={{ width: 300 }}
                  />
                  
                  <Select
                    mode="multiple"
                    placeholder="按标签筛选"
                    value={selectedTags}
                    onChange={setSelectedTags}
                    style={{ minWidth: 200, flex: 1 }}
                    allowClear
                    maxTagCount={3}
                  >
                    {allTags.map(tag => (
                      <Option key={tag} value={tag}>
                        <TagsOutlined /> {tag}
                      </Option>
                    ))}
                  </Select>
                </div>

                {loading ? (
                  <div style={{ textAlign: 'center', padding: '40px 0' }}>
                    <Spin size="large" />
                    <div style={{ marginTop: 16 }}>加载脚本数据中...</div>
                  </div>
                ) : filteredScriptGroups.length === 0 ? (
                  <Empty description="暂无脚本数据" />
                ) : (
                  <Table 
                    dataSource={filteredScriptGroups} 
                    columns={columns}
                    rowKey="job_id"
                    pagination={{ pageSize: 10 }}
                  />
                )}
              </Space>
            </Card>
          </Space>
        </div>

        {/* 脚本详情抽屉 */}
        <Drawer
          title="脚本详情"
          placement="right"
          width={700}
          onClose={closeDetails}
          open={detailsVisible}
          extra={
            <Space>
              <Button onClick={closeDetails}>关闭</Button>
              <Button 
                type="primary" 
                onClick={() => showGenerateScriptsDrawer(currentGroup?.job_id || '')}
              >
                生成更多
              </Button>
            </Space>
          }
        >
          {currentGroup && (
            <Space direction="vertical" style={{ width: '100%' }}>
              <Card 
                title="原文内容" 
                extra={
                  editingOriginalText ? (
                    <Space>
                      <Button onClick={() => setEditingOriginalText(false)}>取消</Button>
                      <Button type="primary" onClick={saveOriginalText}>保存</Button>
                    </Space>
                  ) : (
                    <Button icon={<EditOutlined />} onClick={() => setEditingOriginalText(true)}>
                      编辑
                    </Button>
                  )
                }
              >
                {editingOriginalText ? (
                  <TextArea
                    value={editableOriginalText}
                    onChange={(e) => setEditableOriginalText(e.target.value)}
                    autoSize={{ minRows: 3, maxRows: 10 }}
                  />
                ) : (
                  <Paragraph>{currentGroup.original_text}</Paragraph>
                )}
              </Card>
              
              <Card title="标签">
                <Space wrap>
                  {currentGroup.tags?.map(tag => (
                    <Tag key={tag} color="blue">
                      <TagsOutlined /> {tag}
                    </Tag>
                  ))}
                </Space>
              </Card>
              
              <Divider orientation="left">脚本内容</Divider>
              
              <List
                itemLayout="vertical"
                dataSource={currentGroup.scripts}
                renderItem={(script) => (
                  <List.Item
                    actions={[
                      <Tooltip title="复制内容" key="copy">
                        <Button 
                          type="text" 
                          icon={<CopyOutlined />} 
                          onClick={() => copyScript(script.content)}
                        />
                      </Tooltip>,
                      <Tooltip title={favorites.has(script.id || '') ? "取消收藏" : "收藏"} key="favorite">
                        <Button 
                          type="text" 
                          icon={favorites.has(script.id || '') ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />} 
                          onClick={() => toggleFavorite(script.id || '')}
                        />
                      </Tooltip>
                    ]}
                  >
                    <div style={{ 
                      backgroundColor: favorites.has(script.id || '') ? '#fffbe6' : 'transparent',
                      padding: '16px',
                      borderRadius: '4px',
                      border: favorites.has(script.id || '') ? '1px solid #faad14' : '1px solid #f0f0f0'
                    }}>
                      <Paragraph>{script.content}</Paragraph>
                    </div>
                  </List.Item>
                )}
              />
            </Space>
          )}
        </Drawer>

        {/* 生成更多脚本的抽屉 */}
        <Drawer
          title="生成更多脚本"
          placement="right"
          width={500}
          onClose={() => setGenerateDrawerVisible(false)}
          open={generateDrawerVisible}
          extra={
            <Button 
              type="primary" 
              loading={generatingScripts}
              onClick={handleGenerateMoreScripts}
            >
              开始生成
            </Button>
          }
        >
          <Form layout="vertical">
            <Form.Item label="脚本数量">
              <InputNumber
                min={1}
                max={10}
                value={numScripts}
                onChange={(value) => setNumScripts(value || 3)}
                style={{ width: '100%' }}
              />
            </Form.Item>
            
            <Form.Item label="生成模式">
              <Radio.Group 
                value={overwriteScripts} 
                onChange={(e) => setOverwriteScripts(e.target.value)}
              >
                <Radio value={false}>追加模式（保留现有脚本）</Radio>
                <Radio value={true}>覆盖模式（替换现有脚本）</Radio>
              </Radio.Group>
            </Form.Item>
            
            <Form.Item label="生成提示词">
              <TextArea
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="输入自定义提示词，指导脚本生成方向"
                autoSize={{ minRows: 8, maxRows: 16 }}
                style={{ fontSize: '14px', lineHeight: '1.5' }}
              />
              <div style={{ marginTop: 8 }}>
                <Button 
                  size="small" 
                  type="link" 
                  onClick={() => setCustomPrompt(defaultPrompt)}
                >
                  使用默认提示词
                </Button>
                <div style={{ marginTop: 4 }}>
                  <Text type="secondary">
                    提示：{"{text}"} 将被替换为原文，{"{tags}"} 将被替换为标签，{"{num_scripts}"} 将被替换为脚本数量
                  </Text>
                </div>
              </div>
            </Form.Item>
            
            <Text type="secondary">
              生成过程可能需要一些时间，请耐心等待。生成完成后，请刷新页面查看新生成的脚本。
            </Text>
          </Form>
        </Drawer>
      </App>
    </AppLayout>
  );
};

export default ScriptsPage;
