import {
  Box, Flex, Group, Input, Radio, rem, Text,
} from '@mantine/core';
import { useState } from 'react';
import { RadioResponse } from '../../parser/types';
import { generateErrorMessage } from './utils';
import { ReactMarkdownWrapper } from '../ReactMarkdownWrapper';
import { HorizontalHandler } from './HorizontalHandler';
import classes from './css/Radio.module.css';
import inputClasses from './css/Input.module.css';

export function RadioInput({
  response,
  disabled,
  answer,
  index,
  enumerateQuestions,
  stretch,
  otherValue,
  isLikert,
}: {
  response: RadioResponse;
  disabled: boolean;
  answer: object;
  index: number;
  enumerateQuestions: boolean;
  stretch?: boolean;
  otherValue?: object;
  isLikert?: boolean;
}) {
  const {
    prompt,
    required,
    options,
    leftLabel,
    rightLabel,
    secondaryText,
    horizontal,
    withOther,
  } = response;

  const optionsAsStringOptions = options.map((option) => (typeof option === 'string' ? { value: option, label: option } : option));

  const [otherSelected, setOtherSelected] = useState(false);

  return (
    <Box
      {...(isLikert
        ? {
            p: 'md',
            mb: 'lg',
            style: {
              border: '1px solid var(--mantine-color-gray-3)',
              borderRadius: 8,
              background: 'var(--mantine-color-gray-0)',
            },
          }
        : {})}
    >
      <Radio.Group
        name={`radioInput${response.id}`}
        label={(
          <Flex direction="row" wrap="nowrap" gap={4}>
            {enumerateQuestions && <Box style={{ minWidth: 'fit-content', fontSize: 16, fontWeight: 500 }}>{`${index}. `}</Box>}
            <Box style={{ display: 'block' }} className="no-last-child-bottom-padding">
              <ReactMarkdownWrapper text={prompt} required={required} />
            </Box>
          </Flex>
        )}
        description={secondaryText}
        key={response.id}
        {...answer}
        // This overrides the answers error. Which..is bad?
        error={generateErrorMessage(response, answer, optionsAsStringOptions)}
        style={{ '--input-description-size': 'calc(var(--mantine-font-size-md) - calc(0.125rem * var(--mantine-scale)))' }}
        mb={isLikert ? 0 : 'sm'}
      >
      <Group gap="lg" align="flex-end" mt={horizontal ? 0 : 'sm'}>
        {leftLabel ? <Text>{leftLabel}</Text> : null}
        <HorizontalHandler horizontal={!!horizontal} style={{ flexGrow: 1 }}>
          {optionsAsStringOptions.map((radio) => (
            <div
              key={`${radio.value}-${response.id}`}
              style={{
                display: 'flex',
                flexDirection: horizontal ? 'column' : 'row',
                gap: horizontal ? 'unset' : rem(12),
                flex: stretch ? 1 : 'unset',
                  alignItems: 'center',
                  justifyContent: horizontal ? 'center' : 'flex-start',
                  minWidth: horizontal ? 64 : 'unset',
              }}
            >
              {horizontal && <Text size="sm" style={{ textAlign: 'center' }}>{radio.label}</Text>}
              <Radio
                disabled={disabled}
                value={radio.value}
                label={radio.label}
                styles={{
                  label: { display: !horizontal ? 'initial' : 'none' },
                }}
                onChange={() => setOtherSelected(false)}
                classNames={{ radio: classes.fixDisabled, label: classes.fixDisabledLabel, icon: classes.fixDisabledIcon }}
              />
            </div>
          ))}
          {withOther && (
            <div
              style={{
                display: 'flex',
                flexDirection: horizontal ? 'column' : 'row',
                gap: horizontal ? 'unset' : rem(12),
                flex: stretch ? 1 : 'unset',
                alignItems: 'center',
                  justifyContent: horizontal ? 'center' : 'flex-start',
                  minWidth: horizontal ? 64 : 'unset',
              }}
            >
              {horizontal && <Text size="sm" style={{ textAlign: 'center' }}>Other</Text>}
              <Radio
                disabled={disabled}
                value="other"
                checked={otherSelected}
                onClick={(event) => setOtherSelected(event.currentTarget.checked)}
                label={!horizontal && (
                <Input
                  mt={-8}
                  placeholder="Other"
                  disabled={!otherSelected}
                  {...otherValue}
                  classNames={{ input: inputClasses.fixDisabled }}
                />
                )}
                mt={0}
                classNames={{ radio: classes.fixDisabled, label: classes.fixDisabledLabel, icon: classes.fixDisabledIcon }}
              />
            </div>
          )}
        </HorizontalHandler>
        <Text>{rightLabel}</Text>
      </Group>
      {horizontal && withOther && (
        <Input
          mt="sm"
          placeholder="Other"
          disabled={!otherSelected}
          {...otherValue}
          w={216}
          classNames={{ input: inputClasses.fixDisabled }}
        />
      )}
      </Radio.Group>
    </Box>
  );
}
