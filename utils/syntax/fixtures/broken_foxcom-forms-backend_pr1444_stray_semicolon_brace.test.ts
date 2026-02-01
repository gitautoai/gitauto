/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-var-requires */
import { TimeZone } from '../../../timeZone';
import { getDisplayValueByQuestion } from './getDisplayValueByQuestion';
import localizeToDateString from '../../../localizeToDateString';
import { getValueFromChoices } from './getValueFromChoices';

jest.mock('../../../localizeToDateString');
jest.mock('./getValueFromChoices');

const mockLocalizeToDateString = localizeToDateString as jest.MockedFunction<typeof localizeToDateString>;
const mockGetValueFromChoices = getValueFromChoices as jest.MockedFunction<typeof getValueFromChoices>;

describe('getDisplayValueByQuestion', () => {
  const mockTimeZone: TimeZone = 'Canada/Eastern';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Date value handling', () => {
    it('should format Date value using localizeToDateString', () => {
      const testDate = new Date('2023-12-25T10:30:00Z');
      };
      const question = {
        value: testDate,
      } as any;

      mockLocalizeToDateString.mockReturnValue('2023-12-25');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockLocalizeToDateString).toHaveBeenCalledWith({
        date: testDate,
        timeZone: mockTimeZone,
      });
      expect(result).toBe('2023-12-25');
    });

    it('should format Date value with US timezone', () => {
      const testDate = new Date('2023-01-15T10:30:00Z');
      const usTimeZone: TimeZone = 'America/New_York';
      const question = {
        value: testDate,
      } as any;

      mockLocalizeToDateString.mockReturnValue('2023-01-15');

      const result = getDisplayValueByQuestion(question, usTimeZone);
      };

      expect(mockLocalizeToDateString).toHaveBeenCalledWith({
        date: testDate,
        timeZone: usTimeZone,
      });
      expect(result).toBe('2023-01-15');
    });

    it('should handle Date value with choices present but not use choices', () => {
      const testDate = new Date('2023-06-01T12:00:00Z');
      const question = {
        value: testDate,
        choices: [
          { value: 'option1', text: 'Option 1' },
          { value: 'option2', text: 'Option 2' },
        ],
      } as any;

      mockLocalizeToDateString.mockReturnValue('2023-06-01');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockLocalizeToDateString).toHaveBeenCalledWith({
        date: testDate,
        timeZone: mockTimeZone,
      });
      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('2023-06-01');
    });

    it('should handle invalid Date object', () => {
      const invalidDate = new Date('invalid-date-string');
      const question = {
        value: invalidDate,
      } as any;

      mockLocalizeToDateString.mockReturnValue('Invalid Date');

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockLocalizeToDateString).toHaveBeenCalledWith({
        date: invalidDate,
        timeZone: mockTimeZone,
      });
      expect(result).toBe('Invalid Date');
    });
  });

  describe('choices handling', () => {
    it('should use getValueFromChoices when choices array has items', () => {
      const mockChoices = [
        { value: 'option1', text: 'Option 1' },
        { value: 'option2', text: 'Option 2' },
        { value: 'option3', text: 'Option 3' },
      ];
      const question = {
        value: 'option2',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Option 2');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('option2', mockChoices);
      expect(result).toBe('Option 2');
    });

    it('should handle single choice in array', () => {
      const mockChoices = [{ value: 'only-option', text: 'Only Option' }];
      const question = {
        value: 'only-option',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Only Option');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('only-option', mockChoices);
      expect(result).toBe('Only Option');
    });

    it('should handle choices with numeric values', () => {
      const mockChoices = [
        { value: '1', text: 'One' },
        { value: '2', text: 'Two' },
      ];
      const question = {
        value: '1',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('One');

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('1', mockChoices);
      expect(result).toBe('One');
    });

    it('should handle choices with special characters', () => {
      const mockChoices = [
        { value: 'option-with-dash', text: 'Option With Dash' },
        { value: 'option_with_underscore', text: 'Option With Underscore' },
      ];
      const question = {
        value: 'option-with-dash',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Option With Dash');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('option-with-dash', mockChoices);
      expect(result).toBe('Option With Dash');
    });

    it('should return the original value when choices array is empty', () => {
      const question = {
        value: 'test-value',
        choices: [],
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should return the original value when choices is not present', () => {
      const question = {
        value: 'test-value',
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle when getValueFromChoices returns undefined', () => {
      const mockChoices = [{ value: 'option1', text: 'Option 1' }];
      const question = {
        value: 'non-existent-option',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue(undefined);

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('non-existent-option', mockChoices);
      expect(result).toBeUndefined();
    });

    it('should handle when getValueFromChoices returns null', () => {
      const mockChoices = [{ value: 'option1', text: 'Option 1' }];
      const question = {
        value: 'option1',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue(null as any);

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('option1', mockChoices);
      expect(result).toBeNull();
    });

    it('should handle when getValueFromChoices returns empty string', () => {
      const mockChoices = [{ value: 'option1', text: '' }];
      const question = {
        value: 'option1',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('');

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('option1', mockChoices);
      expect(result).toBe('');
    });
  });

  describe('fallback value handling', () => {
    it('should return string value as-is when no special handling needed', () => {
      const question = {
        value: 'simple-string-value',
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe('simple-string-value');
    });

    it('should return number value as-is', () => {
      const question = {
        value: 42,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(42);
    });

    it('should return boolean true as-is', () => {
      const question = {
        value: true,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(true);
    });

    it('should return null value as-is', () => {
      const question = {
        value: null,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(result).toBeNull();
    });

    it('should return undefined value as-is', () => {
      const question = {
        value: undefined,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBeUndefined();
    });

    it('should return object value as-is', () => {
      const objectValue = { key: 'value', nested: { data: 'test' } };
      const question = {
        value: objectValue,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(objectValue);
    });

    it('should return array value as-is', () => {
      const arrayValue = ['item1', 'item2', 'item3'];
      const question = {
        value: arrayValue,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(result).toBe(arrayValue);
    });

    it('should return zero as-is', () => {
      const question = {
        value: 0,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(0);
    });

    it('should return the original value for empty string', () => {
      const question = {
        value: '',
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe('');
    });

    it('should return the original value for false', () => {
      const question = {
        value: false,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(false);
    });

    it('should return the original value for decimal number', () => {
      const question = {
        value: 3.14159,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(result).toBe(3.14159);
    });

    it('should return NaN as-is', () => {
      const question = {
        value: NaN,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBeNaN();
    });

    it('should return Infinity as-is', () => {
      const question = {
        value: Infinity,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(Infinity);
    });

    it('should return -Infinity as-is', () => {
      const question = {
        value: -Infinity,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(-Infinity);
    });

    it('should return negative numbers as-is', () => {
      const question = {
        value: -42,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(result).toBe(-42);
    });

    it('should return very large numbers as-is', () => {
      const largeNumber = Number.MAX_SAFE_INTEGER;
      const question = {
        value: largeNumber,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(largeNumber);
    });

    it('should return very small numbers as-is', () => {
      const smallNumber = Number.MIN_SAFE_INTEGER;
      const question = {
        value: smallNumber,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(smallNumber);
    });
  });

  describe('edge cases', () => {
    it('should handle question with no value property', () => {
      const question = {} as any;
      };

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBeUndefined();
    });

    it('should handle null question', () => {
      const question = null as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBeUndefined();
    });

    it('should handle undefined question', () => {
      const question = undefined as any;
      };

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBeUndefined();
    });

    it('should work with all supported Canada timezone types', () => {
      const testDate = new Date('2023-12-25T10:30:00Z');
      const canadaTimezones: TimeZone[] = [
        'Canada/Eastern',
        'Canada/Atlantic',
        'Canada/Newfoundland',
        'Canada/Central',
        'Canada/Mountain',
        'Canada/Pacific',
      ];

      canadaTimezones.forEach((timezone) => {
        const question = {
          value: testDate,
        } as any;

        mockLocalizeToDateString.mockReturnValue(`formatted-${timezone}`);

        const result = getDisplayValueByQuestion(question, timezone);

        expect(mockLocalizeToDateString).toHaveBeenCalledWith({
          date: testDate,
          timeZone: timezone,
        });
        expect(result).toBe(`formatted-${timezone}`);
      });
    });

    it('should work with all supported US timezone types', () => {
      const testDate = new Date('2023-12-25T10:30:00Z');
      const usTimezones: TimeZone[] = [
        'America/New_York',
        'America/Chihuahua',
        'America/Chicago',
        'America/Los_Angeles',
        'Pacific/Honolulu',
        'America/Anchorage',
      ];

      usTimezones.forEach((timezone) => {
        const question = {
          value: testDate,
        } as any;

        mockLocalizeToDateString.mockReturnValue(`formatted-${timezone}`);

        const result = getDisplayValueByQuestion(question, timezone);

        expect(mockLocalizeToDateString).toHaveBeenCalledWith({
          date: testDate,
          timeZone: timezone,
        });
        expect(result).toBe(`formatted-${timezone}`);
      });
    });

    it('should handle complex nested object values', () => {
      const complexValue = {
        nested: {
          level2: {
            level3: ['a', 'b', 'c'],
            date: new Date('2023-01-01'),
            boolean: true,
            number: 42,
          },
        },
      };
      const question = {
        value: complexValue,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(result).toBe(complexValue);
    });

    it('should handle function values', () => {
      const functionValue = () => 'test';
      const question = {
        value: functionValue,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(functionValue);
    });

    it('should handle Symbol values', () => {
      const symbolValue = Symbol('test');
      const question = {
        value: symbolValue,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(symbolValue);
    });

    it('should handle BigInt values', () => {
      const bigIntValue = BigInt('123456789012345678901234567890');
      };
      const question = {
        value: bigIntValue,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(bigIntValue);
    });

    it('should handle question with choices property but not an array', () => {
      const question = {
        value: 'test-value',
        choices: 'not-an-array',
      } as any;

      mockGetValueFromChoices.mockReturnValue('test-value');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('test-value', 'not-an-array');
      expect(result).toBe('test-value');
    });

    it('should handle question with choices as object without length', () => {
      const question = {
        value: 'test-value',
        choices: { option1: 'Option One' },
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle Date-like object that is not actually a Date', () => {
      const fakeDateObject = {
        getTime: () => 1234567890,
        toString: () => '2023-01-01',
      };
      const question = {
        value: fakeDateObject,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockLocalizeToDateString).not.toHaveBeenCalled();
      expect(result).toBe(fakeDateObject);
    });

    it('should handle choices with zero length property', () => {
      const mockChoices = { length: 0 } as any;
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle choices with negative length', () => {
      const mockChoices = { length: -1 } as any;
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle choices with non-numeric length', () => {
      const mockChoices = { length: 'not-a-number' } as any;
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle question with null choices', () => {
      const question = {
        value: 'test-value',
        choices: null,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle question with undefined choices', () => {
      const question = {
        value: 'test-value',
        choices: undefined,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle Date object with epoch time 0', () => {
      const epochDate = new Date(0);
      };
      const question = {
        value: epochDate,
      } as any;

      mockLocalizeToDateString.mockReturnValue('1970-01-01');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockLocalizeToDateString).toHaveBeenCalledWith({
        date: epochDate,
        timeZone: mockTimeZone,
      });
      expect(result).toBe('1970-01-01');
    });

    it('should handle Date object with far future date', () => {
      const futureDate = new Date('2099-12-31T23:59:59Z');
      const question = {
        value: futureDate,
      } as any;

      mockLocalizeToDateString.mockReturnValue('2099-12-31');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockLocalizeToDateString).toHaveBeenCalledWith({
        date: futureDate,
        timeZone: mockTimeZone,
      });
      expect(result).toBe('2099-12-31');
    });

    it('should handle Date object with far past date', () => {
      const pastDate = new Date('1900-01-01T00:00:00Z');
      };
      const question = {
        value: pastDate,
      } as any;

      mockLocalizeToDateString.mockReturnValue('1900-01-01');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockLocalizeToDateString).toHaveBeenCalledWith({
        date: pastDate,
        timeZone: mockTimeZone,
      });
      expect(result).toBe('1900-01-01');
    });

    it('should handle array values with mixed types', () => {
      const mixedArray = [1, 'string', true, null, undefined, { key: 'value' }];
      const question = {
        value: mixedArray,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(mixedArray);
    });

    it('should handle empty object values', () => {
      const emptyObject = {};
      };
      const question = {
        value: emptyObject,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(emptyObject);
    });

    it('should handle empty array values', () => {
      const emptyArray: any[] = [];
      const question = {
        value: emptyArray,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(emptyArray);
    });

    it('should handle Map objects', () => {
      const mapValue = new Map([
        ['key1', 'value1'],
        ['key2', 'value2'],
      ]);
      const question = {
        value: mapValue,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(mapValue);
    });

    it('should handle Set objects', () => {
      const setValue = new Set([1, 2, 3, 'string']);
      };
      const question = {
        value: setValue,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(setValue);
    });

    it('should handle WeakMap objects', () => {
      const weakMapValue = new WeakMap();
      const question = {
        value: weakMapValue,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(weakMapValue);
    });

    it('should handle WeakSet objects', () => {
      const weakSetValue = new WeakSet();
      };
      const question = {
        value: weakSetValue,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(weakSetValue);
    });

    it('should handle RegExp objects', () => {
      const regexValue = /test-pattern/gi;
      const question = {
        value: regexValue,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(regexValue);
    });

    it('should handle Error objects', () => {
      const errorValue = new Error('Test error');
      };
      const question = {
        value: errorValue,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(errorValue);
    });

    it('should handle Promise objects', () => {
      const promiseValue = Promise.resolve('test');
      const question = {
        value: promiseValue,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(promiseValue);
    });

    it('should handle ArrayBuffer objects', () => {
      const bufferValue = new ArrayBuffer(8);
      const question = {
        value: bufferValue,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(result).toBe(bufferValue);
    });

    it('should handle TypedArray objects', () => {
      const typedArrayValue = new Uint8Array([1, 2, 3, 4]);
      const question = {
        value: typedArrayValue,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(typedArrayValue);
    });

    it('should handle class instances', () => {
      class TestClass {
        constructor(public value: string) {}
      }
      const classInstance = new TestClass('test');
      const question = {
        value: classInstance,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(result).toBe(classInstance);
    });

    it('should handle circular reference objects', () => {
      const circularObj: any = { name: 'test' };
      circularObj.self = circularObj;
      const question = {
        value: circularObj,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(circularObj);
    });

    it('should handle question object with additional properties', () => {
      const question = {
        value: 'test-value',
        name: 'test-question',
        type: 'text',
        title: 'Test Question',
        isRequired: true,
        additionalProp: 'extra',
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe('test-value');
    });

    it('should handle choices array with very large length', () => {
      const largeChoicesArray = new Array(10000).fill(null).map((_, i) => ({
        value: `option${i}`,
        text: `Option ${i}`,
      }));
      const question = {
        value: 'option5000',
        choices: largeChoicesArray,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Option 5000');

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('option5000', largeChoicesArray);
      expect(result).toBe('Option 5000');
    });

    it('should handle choices array with length property but no actual array methods', () => {
      const pseudoArray = {
        length: 3,
        0: { value: 'first', text: 'First' },
        1: { value: 'second', text: 'Second' },
        2: { value: 'third', text: 'Third' },
      };
      const question = {
        value: 'second',
        choices: pseudoArray,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Second');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('second', pseudoArray);
      expect(result).toBe('Second');
    });

    it('should handle Date subclass instances', () => {
      class CustomDate extends Date {
        customProperty = 'custom';
      }
      const customDate = new CustomDate('2023-01-01T12:00:00Z');
      const question = {
        value: customDate,
      } as any;

      mockLocalizeToDateString.mockReturnValue('2023-01-01');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockLocalizeToDateString).toHaveBeenCalledWith({
        date: customDate,
        timeZone: mockTimeZone,
      });
      expect(result).toBe('2023-01-01');
    });

    it('should handle question with getter/setter properties', () => {
      const question = {
        _value: 'internal-value',
        get value() {
          return this._value;
        },
        set value(val) {
          this._value = val;
        },
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe('internal-value');
    });

    it('should handle question with computed value property', () => {
      const question = {
        baseValue: 'base',
        get value() {
          return `${this.baseValue}-computed`;
        },
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(result).toBe('base-computed');
    });

    it('should handle question with value property that throws when accessed', () => {
      const question = {
        get value() {
          throw new Error('Cannot access value');
        },
      } as any;

      expect(() => getDisplayValueByQuestion(question, mockTimeZone)).toThrow('Cannot access value');
    });

    it('should handle question with choices property that throws when accessed', () => {
      const question = {
        value: 'test-value',
        get choices() {
          throw new Error('Cannot access choices');
        },
      } as any;

      expect(() => getDisplayValueByQuestion(question, mockTimeZone)).toThrow('Cannot access choices');
    });

    it('should handle all primitive wrapper objects', () => {
      const stringWrapper = new String('wrapped string');
      const numberWrapper = new Number(42);
      const booleanWrapper = new Boolean(true);

      const stringQuestion = { value: stringWrapper } as any;
      };
      const numberQuestion = { value: numberWrapper } as any;
      const booleanQuestion = { value: booleanWrapper } as any;

      expect(getDisplayValueByQuestion(stringQuestion, mockTimeZone)).toBe(stringWrapper);
      expect(getDisplayValueByQuestion(numberQuestion, mockTimeZone)).toBe(numberWrapper);
      expect(getDisplayValueByQuestion(booleanQuestion, mockTimeZone)).toBe(booleanWrapper);
    });
  });

  describe('mock behavior verification', () => {
    it('should not call any mocked functions when returning primitive values', () => {
      const question = {
        value: 'simple-string',
      } as any;

      getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockLocalizeToDateString).not.toHaveBeenCalled();
      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
    });

    it('should call localizeToDateString exactly once for Date values', () => {
      const testDate = new Date('2023-01-01');
      const question = {
        value: testDate,
      } as any;

      mockLocalizeToDateString.mockReturnValue('formatted-date');

      getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockLocalizeToDateString).toHaveBeenCalledTimes(1);
      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
    });

    it('should call getValueFromChoices exactly once for choices with length > 0', () => {
      const mockChoices = [{ value: 'test', text: 'Test' }];
      };
      const question = {
        value: 'test',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Test');

      getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledTimes(1);
      expect(mockLocalizeToDateString).not.toHaveBeenCalled();
    });

    it('should preserve mock call order when multiple tests run', () => {
      const testDate = new Date('2023-01-01');
      const question1 = { value: testDate } as any;
      const question2 = { value: 'string', choices: [{ value: 'string', text: 'String' }] } as any;
      mockGetValueFromChoices.mockReturnValue('choice-result');

      getDisplayValueByQuestion(question1, mockTimeZone);
      getDisplayValueByQuestion(question2, mockTimeZone);

      expect(mockLocalizeToDateString).toHaveBeenCalledTimes(1);
      expect(mockGetValueFromChoices).toHaveBeenCalledTimes(1);
    });

    it('should handle mock function return values correctly', () => {
      const testDate = new Date('2023-01-01');
      const question = { value: testDate } as any;
      };

      mockLocalizeToDateString.mockReturnValue('string-result');
      expect(getDisplayValueByQuestion(question, mockTimeZone)).toBe('string-result');

      mockLocalizeToDateString.mockReturnValue(null as any);
      expect(getDisplayValueByQuestion(question, mockTimeZone)).toBe(null);

      mockLocalizeToDateString.mockReturnValue(undefined as any);
      expect(getDisplayValueByQuestion(question, mockTimeZone)).toBe(undefined);

      mockLocalizeToDateString.mockReturnValue(42 as any);
      expect(getDisplayValueByQuestion(question, mockTimeZone)).toBe(42);
    });

    it('should handle mock function exceptions', () => {
      const testDate = new Date('2023-01-01');
      const question = { value: testDate } as any;

      mockLocalizeToDateString.mockImplementation(() => {
        throw new Error('Mock error');
      });

      expect(() => getDisplayValueByQuestion(question, mockTimeZone)).toThrow('Mock error');
    });
  });

  describe('type coercion and casting', () => {
    it('should handle value casting to string in getValueFromChoices call', () => {
      const mockChoices = [{ value: '123', text: 'One Two Three' }];
      const question = {
        value: 123,
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('One Two Three');

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockGetValueFromChoices).toHaveBeenCalledWith(123, mockChoices);
      expect(result).toBe('One Two Three');
    });

    it('should handle Date casting in localizeToDateString call', () => {
      const testDate = new Date('2023-01-01');
      const question = {
        value: testDate,
      } as any;

      mockLocalizeToDateString.mockReturnValue('formatted-date');

      getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockLocalizeToDateString).toHaveBeenCalledWith({
        date: testDate,
        timeZone: mockTimeZone,
      });
    });

    it('should handle optional chaining for question properties', () => {
      let question = null as any;
      expect(getDisplayValueByQuestion(question, mockTimeZone)).toBeUndefined();

      question = { value: 'test' } as any;
      expect(getDisplayValueByQuestion(question, mockTimeZone)).toBe('test');

      question = { value: 'test', choices: null } as any;
      expect(getDisplayValueByQuestion(question, mockTimeZone)).toBe('test');
    });
  });

  describe('return value consistency', () => {
    it('should maintain return type consistency across all branches', () => {
      const dateQuestion = { value: new Date() } as any;
      mockLocalizeToDateString.mockReturnValue('date-string');
      const dateResult = getDisplayValueByQuestion(dateQuestion, mockTimeZone);
      };
      expect(typeof dateResult).toBe('string');

      const choicesQuestion = { value: 'test', choices: [{ value: 'test', text: 'Test' }] } as any;
      mockGetValueFromChoices.mockReturnValue('choice-text');
      const choicesResult = getDisplayValueByQuestion(choicesQuestion, mockTimeZone);
      expect(typeof choicesResult).toBe('string');

      const fallbackQuestion = { value: 'original' } as any;
      const fallbackResult = getDisplayValueByQuestion(fallbackQuestion, mockTimeZone);
      expect(typeof fallbackResult).toBe('string');
    });

    it('should handle return value type preservation', () => {
      const testDate = new Date();
      };
      const question = { value: testDate } as any;

      const mockReturnValue = { custom: 'object' };
      mockLocalizeToDateString.mockReturnValue(mockReturnValue as any);

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(result).toBe(mockReturnValue);
      expect(result).toEqual({ custom: 'object' });
    });
  });

  describe('branch coverage for choices condition', () => {
    it('should handle choices with length exactly 1', () => {
      const mockChoices = [{ value: 'single', text: 'Single Option' }];
      };
      const question = {
        value: 'single',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Single Option');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('single', mockChoices);
      expect(result).toBe('Single Option');
    });

    it('should not call getValueFromChoices when choices length is exactly 0', () => {
      const question = {
        value: 'test-value',
        choices: [],
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle choices with fractional length', () => {
      const mockChoices = { length: 1.5 } as any;
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('result');

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('test-value', mockChoices);
      expect(result).toBe('result');
    });

    it('should handle choices when question.choices is null and value is not Date', () => {
      const question = {
        value: 'string-value',
        choices: null,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('string-value');
    });

    it('should handle choices when question.choices is undefined and value is not Date', () => {
      const question = {
        value: 'string-value',
        choices: undefined,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('string-value');
    });

    it('should handle choices when question.choices.length is null', () => {
      const mockChoices = { length: null } as any;
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle choices when question.choices.length is undefined', () => {
      const mockChoices = { length: undefined } as any;
      };
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should call getValueFromChoices when choices.length is greater than 0', () => {
      const mockChoices = [
        { value: 'opt1', text: 'Option 1' },
        { value: 'opt2', text: 'Option 2' },
      ];
      const question = {
        value: 'opt1',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Option 1');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('opt1', mockChoices);
      expect(result).toBe('Option 1');
    });

    it('should handle empty array choices with non-Date value', () => {
      const question = {
        value: 123,
        choices: [],
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe(123);
    });

    it('should handle empty array choices with null value', () => {
      const question = {
        value: null,
        choices: [],
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBeNull();
    });

    it('should handle empty array choices with undefined value', () => {
      const question = {
        value: undefined,
        choices: [],
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBeUndefined();
    });

    it('should handle empty array choices with boolean value', () => {
      const question = {
        value: true,
        choices: [],
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe(true);
    });

    it('should handle empty array choices with object value', () => {
      const objectValue = { key: 'value' };
      const question = {
        value: objectValue,
        choices: [],
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe(objectValue);
    });

    it('should handle question with getter that returns choices on first access but undefined on second', () => {
      let accessCount = 0;
      const question = {
        value: 'test-value',
        get choices() {
          accessCount++;
          if (accessCount === 1) {
            return [{ value: 'test-value', text: 'Test Text' }];
          }
          return undefined;
        },
      } as any;

      mockGetValueFromChoices.mockReturnValue(undefined);

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('test-value', undefined);
      expect(result).toBeUndefined();
    });

    it('should handle choices with length property equal to Number.MAX_SAFE_INTEGER', () => {
      const mockChoices = { length: Number.MAX_SAFE_INTEGER } as any;
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('result');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('test-value', mockChoices);
      expect(result).toBe('result');
    });

    it('should handle choices with boolean length property true', () => {
      const mockChoices = { length: true } as any;
      };
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('result');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('test-value', mockChoices);
      expect(result).toBe('result');
    });

    it('should handle choices with boolean length property false', () => {
      const mockChoices = { length: false } as any;
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle choices with string length property that coerces to number > 0', () => {
      const mockChoices = { length: '5' } as any;
      };
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('result');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('test-value', mockChoices);
      expect(result).toBe('result');
    });

    it('should handle choices with string length property that coerces to 0', () => {
      const mockChoices = { length: '0' } as any;
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle choices with object length property', () => {
      const mockChoices = { length: {} } as any;
      };
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle choices with array length property', () => {
      const mockChoices = { length: [1, 2, 3] } as any;
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle choices with empty array length property', () => {
      const mockChoices = { length: [] } as any;
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle question with Proxy that changes choices between accesses', () => {
      let accessCount = 0;
      const proxyQuestion = new Proxy(
        { value: 'test-value' },
        {
          get(target: any, prop: string) {
            if (prop === 'choices') {
              accessCount++;
              if (accessCount === 1) {
                return [{ value: 'test-value', text: 'Test Text' }];
              }
              return [{ value: 'test-value', text: 'Test Text' }];
            }
            return target[prop];
          },
        }
      );

      mockGetValueFromChoices.mockReturnValue('Test Text');

      const result = getDisplayValueByQuestion(proxyQuestion as any, mockTimeZone);

      expect(result).toBe('Test Text');
    });

    it('should handle question with Proxy that changes value between accesses', () => {
      let accessCount = 0;
      const mockChoices = [{ value: 'test', text: 'Test' }];
      };
      const proxyQuestion = new Proxy(
        { value: 'test' },
        {
          get(target: any, prop: string) {
            if (prop === 'value') {
              return target.value;
            }
            if (prop === 'choices') {
              accessCount++;
              if (accessCount <= 2) {
                return mockChoices;
              }
              return undefined;
            }
            return target[prop];
          },
        }
      );

      mockGetValueFromChoices.mockReturnValue('Test');

      const result = getDisplayValueByQuestion(proxyQuestion as any, mockTimeZone);

      expect(result).toBe('Test');
    });

    it('should handle question where choices.length is accessed via getter with side effects', () => {
      let lengthAccessCount = 0;
      const mockChoices = {
        get length() {
          lengthAccessCount++;
          return lengthAccessCount === 1 ? 1 : 0;
        },
        find: () => ({ text: 'Result' }),
      };
      const question = {
        value: 'test',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Result');

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      expect(result).toBe('Result');
    });
  });

  describe('additional branch coverage tests', () => {
    it('should handle question with choices array containing non-string value types', () => {
      const mockChoices = [
        { value: 123, text: 'Number Value' },
        { value: true, text: 'Boolean Value' },
      ] as any;
      const question = {
        value: 123,
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Number Value');

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockGetValueFromChoices).toHaveBeenCalledWith(123, mockChoices);
      expect(result).toBe('Number Value');
    });

    it('should handle question where value is array and choices exist', () => {
      const mockChoices = [
        { value: 'opt1', text: 'Option 1' },
        { value: 'opt2', text: 'Option 2' },
      ];
      const question = {
        value: ['opt1', 'opt2'],
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue(undefined);

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith(['opt1', 'opt2'], mockChoices);
      expect(result).toBeUndefined();
    });

    it('should handle question where value is object and choices exist', () => {
      const mockChoices = [{ value: 'test', text: 'Test' }];
      const objectValue = { key: 'value' };
      const question = {
        value: objectValue,
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue(undefined);

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith(objectValue, mockChoices);
      expect(result).toBeUndefined();
    });

    it('should handle question where value is null and choices exist with length > 0', () => {
      const mockChoices = [
        { value: 'option1', text: 'Option 1' },
        { value: 'option2', text: 'Option 2' },
      ];
      const question = {
        value: null,
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue(undefined);

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockGetValueFromChoices).toHaveBeenCalledWith(null, mockChoices);
      expect(result).toBeUndefined();
    });

    it('should handle choices with length property as getter that returns positive number', () => {
      const mockChoices = {
        get length() {
          return 2;
        },
        0: { value: 'opt1', text: 'Option 1' },
        1: { value: 'opt2', text: 'Option 2' },
      };
      const question = {
        value: 'opt1',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Option 1');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('opt1', mockChoices);
      expect(result).toBe('Option 1');
    });

    it('should handle choices with length property as getter that returns exactly 0', () => {
      const mockChoices = {
        get length() {
          return 0;
        },
      };
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle choices with length property as getter that returns negative number', () => {
      const mockChoices = {
        get length() {
          return -5;
        },
      };
      const question = {
        value: 'test-value',
        choices: mockChoices,
      } as any;

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).not.toHaveBeenCalled();
      expect(result).toBe('test-value');
    });

    it('should handle choices array with non-string value types', () => {
      const mockChoices = [
        { value: 'option1', text: 'Option 1' },
        { value: 'option2', text: 'Option 2' },
      ];
      const question = {
        value: null,
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue(undefined);

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockGetValueFromChoices).toHaveBeenCalledWith(null, mockChoices);
      expect(result).toBeUndefined();
    });

    it('should handle choices array with undefined value', () => {
      const mockChoices = [
        { value: 'option1', text: 'Option 1' },
        { value: 'option2', text: 'Option 2' },
      ];
      const question = {
        value: undefined,
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue(undefined);

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith(undefined, mockChoices);
      expect(result).toBeUndefined();
    });

    it('should handle choices array with numeric value', () => {
      const mockChoices = [
        { value: '1', text: 'One' },
        { value: '2', text: 'Two' },
      ];
      const question = {
        value: 1,
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue(undefined);

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith(1, mockChoices);
      expect(result).toBeUndefined();
    });

    it('should handle choices array with boolean value', () => {
      const mockChoices = [
        { value: 'true', text: 'Yes' },
        { value: 'false', text: 'No' },
      ];
      const question = {
        value: true,
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue(undefined);

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith(true, mockChoices);
      expect(result).toBeUndefined();
    });

    it('should handle choices array with object value', () => {
      const mockChoices = [
        { value: 'obj1', text: 'Object 1' },
        { value: 'obj2', text: 'Object 2' },
      ];
      const objectValue = { key: 'value' };
      };
      const question = {
        value: objectValue,
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue(undefined);

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith(objectValue, mockChoices);
      expect(result).toBeUndefined();
    });

    it('should handle choices array with array value', () => {
      const mockChoices = [
        { value: 'arr1', text: 'Array 1' },
        { value: 'arr2', text: 'Array 2' },
      ];
      const arrayValue = ['item1', 'item2'];
      const question = {
        value: arrayValue,
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue(undefined);

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith(arrayValue, mockChoices);
      expect(result).toBeUndefined();
    });

    it('should handle choices with length exactly 1 covering the true branch of choices condition', () => {
      const mockChoices = [{ value: 'only-choice', text: 'Only Choice Available' }];
      const question = {
        value: 'only-choice',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Only Choice Available');

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };
      expect(mockGetValueFromChoices).toHaveBeenCalledWith('only-choice', mockChoices);
      expect(result).toBe('Only Choice Available');
    });
  });

  describe('optional chaining branch coverage for line 15', () => {
    it('should handle choices with valid question object ensuring optional chaining branch is covered', () => {
      const mockChoices = [
        { value: 'test-option', text: 'Test Option' },
      ];
      const question = {
        value: 'test-option',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Test Option');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('test-option', mockChoices);
      expect(result).toBe('Test Option');
      expect(question.choices).toBeDefined();
    });
  });

  describe('uncovered branch coverage for line 15', () => {
    it('should pass choices array directly to getValueFromChoices when condition is met', () => {
      const mockChoices = [
        { value: 'choice1', text: 'Choice 1' },
        { value: 'choice2', text: 'Choice 2' },
      ];
      const question = {
        value: 'choice1',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Choice 1');
      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('choice1', mockChoices);
      expect(result).toBe('Choice 1');
    });
  });

  describe('additional optional chaining branch coverage', () => {
    it('should handle question with choices when question object is defined', () => {
      const mockChoices = [
        { value: 'option1', text: 'Option 1' },
        { value: 'option2', text: 'Option 2' },
      ];
      const question = {
        value: 'option1',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Option 1');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('option1', mockChoices);
      expect(result).toBe('Option 1');
    });

    it('should handle question where choices is accessed multiple times in the condition and return', () => {
      const mockChoices = [
        { value: 'test', text: 'Test Value' },
      ];
      const question = {
        value: 'test',
        choices: mockChoices,
      } as any;

      mockGetValueFromChoices.mockReturnValue('Test Value');

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      };

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('test', mockChoices);
      expect(result).toBe('Test Value');
    });

    it('should verify optional chaining evaluates to defined value when passing to getValueFromChoices', () => {
      const mockChoices = [{ value: 'val', text: 'Value' }];
      const question = { value: 'val', choices: mockChoices } as any;
      mockGetValueFromChoices.mockReturnValue('Value');

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith('val', mockChoices);
      expect(result).toBe('Value');
    });

    it('should handle question with choices defined via Object.defineProperty', () => {
      const mockChoices = [{ value: 'test', text: 'Test' }];
      };
      const question = { value: 'test' } as any;
      Object.defineProperty(question, 'choices', {
        get() {
          return mockChoices;
        },
        enumerable: true,
      });
      mockGetValueFromChoices.mockReturnValue('Test');

      const result = getDisplayValueByQuestion(question, mockTimeZone);
      expect(result).toBe('Test');
    });

    it('should handle non-string value types when choices exist', () => {
      const mockChoices = [
        { value: '123', text: 'One Two Three' },
        { value: 'true', text: 'Yes' },
      ];
      const question = { value: null, choices: mockChoices } as any;
      mockGetValueFromChoices.mockReturnValue(undefined);

      const result = getDisplayValueByQuestion(question, mockTimeZone);

      expect(mockGetValueFromChoices).toHaveBeenCalledWith(null, mockChoices);
      expect(result).toBeUndefined();
    });
  });
});
